"""
AI Agent module.

Contains the UIAgent class that handles file operations and Claude interactions.
"""

import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List
import anthropic

from .config import (
    TARGET_PROJECT_DIR,
    ALLOWED_EXTENSIONS,
    CLAUDE_MODEL,
    SYSTEM_PROMPT,
    validate_target_path
)
from . import database as db

logger = logging.getLogger(__name__)


class UIAgent:
    """Agent that handles file operations and Claude interactions via web interface."""

    def __init__(self, api_key: str, model: str = CLAUDE_MODEL):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history = []
        self.capabilities = self._get_capabilities()
        self.app_urls = self._get_app_urls()
        logger.info("UIAgent initialized")

    def _get_app_urls(self) -> str:
        """Return application URLs for context."""
        from . import routes_generator
        return f"""
Application URLs:
- AI Agent Backend: http://localhost:8080
- AI Agent Frontend: http://localhost:4000
- Target Project: {TARGET_PROJECT_DIR}

Key Endpoints:
- API Status: http://localhost:8080/api/status
- Routes Info: http://localhost:8080/api/routes/info
- Export Routes: POST http://localhost:8080/api/routes/export
"""

    def get_target_routes_context(self, app=None) -> str:
        """Get target project routes for AI context."""
        from . import routes_generator
        if app:
            return routes_generator.get_routes_for_ai_context(app)
        else:
            # Scan target project only
            target_info = routes_generator.scan_target_project_routes()
            context = f"Target Project: {target_info.get('target_project', 'N/A')}\n"
            context += f"Routes Found: {target_info.get('routes_found', 0)}\n\n"
            for route in target_info.get('routes', []):
                methods = '/'.join(route['methods'])
                context += f"[{methods}] {route['path']} ({route['framework']}) - {route['file']}\n"
            return context

    def _get_capabilities(self) -> str:
        """Return a description of agent capabilities for self-awareness."""
        return """
Available capabilities:
- Read files from the target project directory
- Modify files using natural language instructions
- List and browse project files
- Smart task processing (auto-identifies relevant files)
- General conversation and Q&A
- Track users, projects, and tickets
- Record change history for all modifications
- Save and export AI findings/context

API endpoints:
- POST /api/chat - General conversation
- POST /api/task - Smart task (two-step: identify files, then analyze)
- POST /api/file/read - Read a specific file
- POST /api/file/modify - Modify a file with instructions
- GET /api/files - List available files
- GET /api/status - Get agent status
- GET /api/routes - List all API routes
- GET/POST /api/users - Manage users (admin, tester, developer)
- GET/POST /api/projects - Manage projects
- GET/POST /api/tickets - Manage tickets (bug, feature, task, improvement)
- GET /api/changes - View change history
- GET/POST /api/context - AI findings and summaries
- POST /api/context/export - Export findings to markdown file
"""

    def read_file(self, file_path: str) -> Optional[Dict]:
        """Read a file from target directory."""
        try:
            target_file = TARGET_PROJECT_DIR / file_path

            # Safety validation
            if not validate_target_path(target_file):
                logger.warning(f"Safety check failed for: {target_file}")
                return {"error": "File access denied - safety check failed"}

            if not target_file.exists():
                return {"error": f"File not found: {file_path}"}

            content = target_file.read_text(encoding='utf-8')
            logger.info(f"File read successfully: {file_path}")

            return {
                "path": str(file_path),
                "content": content,
                "size": len(content),
                "extension": target_file.suffix
            }

        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return {"error": str(e)}

    def list_files(self, directory: str = ".") -> Dict:
        """List files in target directory."""
        try:
            target_dir = TARGET_PROJECT_DIR / directory

            if not target_dir.exists() or not target_dir.is_dir():
                return {"error": "Directory not found"}

            files = []
            for item in target_dir.iterdir():
                if item.is_file() and item.suffix in ALLOWED_EXTENSIONS:
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(TARGET_PROJECT_DIR)),
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime
                    })

            logger.info(f"Listed {len(files)} files in {directory}")
            return {"files": files, "directory": directory}

        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return {"error": str(e)}

    def propose_file_change(self, file_path: str, instruction: str, ticket_id: int = None) -> Optional[Dict]:
        """Propose a file change without applying it. Returns proposed change for review."""
        try:
            # Step 1: Read the file
            file_data = self.read_file(file_path)
            if "error" in file_data:
                return file_data

            original_content = file_data["content"]

            # Step 2: Send to Claude with instruction
            logger.info(f"Asking Claude to propose changes for: {file_path}")

            prompt = f"""Please modify this file according to the instruction.
Return ONLY the complete modified file content, no explanations or markdown code blocks.

Instruction: {instruction}

Current file content:
{original_content}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system="You are a code assistant. Return only the modified file content, nothing else.",
                messages=[{"role": "user", "content": prompt}]
            )

            proposed_content = response.content[0].text

            # Step 3: Store as proposed change
            change_id = db.create_proposed_change(
                file_path=file_path,
                original_content=original_content,
                proposed_content=proposed_content,
                change_description=instruction,
                ticket_id=ticket_id
            )

            logger.info(f"Created proposed change #{change_id} for {file_path}")

            return {
                "status": "proposed",
                "change_id": change_id,
                "file_path": file_path,
                "original_content": original_content,
                "proposed_content": proposed_content,
                "description": instruction
            }

        except Exception as e:
            logger.error(f"Error proposing file change: {e}")
            return {"error": str(e)}

    def apply_proposed_change(self, change_id: int) -> Optional[Dict]:
        """Apply a previously proposed change."""
        try:
            change = db.get_proposed_change(change_id)
            if not change:
                return {"error": "Proposed change not found"}

            if change['status'] != 'pending':
                return {"error": f"Change already {change['status']}"}

            # Write the proposed content to file
            target_file = TARGET_PROJECT_DIR / change['file_path']

            if not validate_target_path(target_file):
                return {"error": "Safety check failed on write"}

            target_file.write_text(change['proposed_content'], encoding='utf-8')

            # Update status
            db.update_proposed_change_status(change_id, 'accepted')

            # Record in changes history
            db.record_change(
                project_id=None,
                files_affected=[change['file_path']],
                change_type="modify",
                change_summary=change['change_description'][:200],
                ai_response=change['proposed_content'][:500],
                ticket_id=change.get('ticket_id')
            )

            logger.info(f"Applied proposed change #{change_id} to {change['file_path']}")

            return {
                "status": "applied",
                "change_id": change_id,
                "file_path": change['file_path']
            }

        except Exception as e:
            logger.error(f"Error applying proposed change: {e}")
            return {"error": str(e)}

    def reject_proposed_change(self, change_id: int) -> Optional[Dict]:
        """Reject a proposed change."""
        try:
            change = db.get_proposed_change(change_id)
            if not change:
                return {"error": "Proposed change not found"}

            if change['status'] != 'pending':
                return {"error": f"Change already {change['status']}"}

            db.update_proposed_change_status(change_id, 'rejected')
            logger.info(f"Rejected proposed change #{change_id}")

            return {
                "status": "rejected",
                "change_id": change_id
            }

        except Exception as e:
            logger.error(f"Error rejecting proposed change: {e}")
            return {"error": str(e)}

    def modify_file_with_claude(self, file_path: str, instruction: str) -> Optional[Dict]:
        """Read file, send to Claude with instruction, and write back result."""
        try:
            # Step 1: Read the file
            file_data = self.read_file(file_path)
            if "error" in file_data:
                return file_data

            content = file_data["content"]

            # Step 2: Send to Claude with instruction
            logger.info(f"Sending file to Claude with instruction: {instruction[:50]}...")

            self.conversation_history.append({
                "role": "user",
                "content": f"Please perform the following operation on this content:\n\n{instruction}\n\nContent:\n\n{content}"
            })

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=self.conversation_history
            )

            modified_content = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": modified_content
            })

            # Step 3: Write back to file
            target_file = TARGET_PROJECT_DIR / file_path

            # Safety check before writing
            if not validate_target_path(target_file):
                return {"error": "Safety check failed on write"}

            target_file.write_text(modified_content, encoding='utf-8')
            logger.info(f"File modified and saved: {file_path}")

            # Record change in database
            db.record_change(
                project_id=None,
                files_affected=[file_path],
                change_type="modify",
                change_summary=instruction[:200],
                ai_response=modified_content[:500]
            )

            return {
                "status": "success",
                "path": file_path,
                "original_size": len(content),
                "modified_size": len(modified_content),
                "preview": modified_content[:500] + "..." if len(modified_content) > 500 else modified_content
            }

        except Exception as e:
            logger.error(f"Error modifying file: {e}")
            return {"error": str(e)}

    def chat(self, user_message: str, app=None) -> str:
        """Send a message to Claude and get a response."""
        try:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Include routes context if question seems related
            routes_context = ""
            route_keywords = ['route', 'endpoint', 'api', 'url', 'path', 'navigate']
            if any(kw in user_message.lower() for kw in route_keywords):
                routes_context = f"\n\nTarget Project Routes:\n{self.get_target_routes_context(app)}"

            system_with_capabilities = f"""You are a helpful AI assistant that helps users manage files and content. Be concise and helpful.

{self.capabilities}

{self.app_urls}
{routes_context}

If users ask what you can do, refer to these capabilities. If they ask about routes or APIs, use the routes information provided."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_with_capabilities,
                messages=self.conversation_history
            )

            assistant_message = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            logger.info("Chat response generated")
            return assistant_message

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error: {str(e)}"

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def save_finding(self, content: str, title: str = None, context_type: str = "finding", tags: List[str] = None) -> int:
        """Save an AI finding/context to the database."""
        context_id = db.save_ai_context(
            content=content,
            context_type=context_type,
            title=title,
            tags=tags
        )
        logger.info(f"Saved AI context: {title or 'Untitled'} (ID: {context_id})")
        return context_id

    def export_context(self, filepath: str = None) -> str:
        """Export all AI context to a markdown file."""
        from .config import DEMO_DIR
        if not filepath:
            filepath = str(DEMO_DIR / "agentic_ai_context.md")
        return db.export_ai_context_to_file(filepath)

    def fetch_target_blueprint(self, project_id: int = None) -> Dict:
        """Fetch blueprint from target project's API."""
        try:
            # Get project backend URL
            if project_id:
                project = db.get_project_by_id(project_id)
            else:
                projects = db.get_projects()
                project = projects[0] if projects else None

            if not project or not project.get('backend_url'):
                return {"error": "No project backend URL configured"}

            backend_url = project['backend_url']

            # Try blueprint_json first, then blueprint
            for endpoint in ['/api/blueprint_json', '/api/blueprint']:
                try:
                    response = requests.get(f"{backend_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            return {
                                "success": True,
                                "endpoint": endpoint,
                                "data": data
                            }
                        except ValueError:
                            # Non-JSON response, try next endpoint
                            continue
                except requests.exceptions.ConnectionError:
                    return {"error": f"Cannot connect to {backend_url}. Is the target project running?"}
                except requests.exceptions.Timeout:
                    return {"error": f"Connection to {backend_url} timed out"}
                except Exception as e:
                    continue

            return {"error": f"Could not fetch blueprint from {backend_url}. Endpoints /api/blueprint_json and /api/blueprint not available."}

        except Exception as e:
            logger.error(f"Error fetching blueprint: {e}")
            return {"error": str(e)}

    def get_target_api_context(self, project_id: int = None) -> str:
        """Get formatted API context from target project for AI prompts."""
        blueprint = self.fetch_target_blueprint(project_id)

        if blueprint.get('error'):
            return f"[Target API context unavailable: {blueprint['error']}]"

        data = blueprint.get('data', {})

        # Format the blueprint data for AI context
        context = "\n=== TARGET PROJECT API BLUEPRINT ===\n"

        if isinstance(data, dict):
            # Handle api_routes format from ecommerce project
            if 'api_routes' in data:
                api_routes = data['api_routes']
                context += f"Total Route Groups: {len(api_routes)}\n\n"
                for group_name, group_info in api_routes.items():
                    prefix = group_info.get('prefix', '')
                    file = group_info.get('file', '')
                    endpoints = group_info.get('endpoints', [])
                    context += f"## {group_name.upper()} ({prefix})\n"
                    context += f"   File: {file}\n"
                    for endpoint in endpoints:
                        context += f"   - {endpoint}\n"
                    context += "\n"

            # Handle test_credentials (dict of dicts format)
            if 'test_credentials' in data:
                context += "## TEST CREDENTIALS\n"
                creds = data['test_credentials']
                if isinstance(creds, dict):
                    for role, info in creds.items():
                        if isinstance(info, dict):
                            context += f"   - {role}: {info.get('email', '')} / {info.get('password', '')}\n"
                        else:
                            context += f"   - {role}: {info}\n"
                elif isinstance(creds, list):
                    for cred in creds:
                        if isinstance(cred, dict):
                            context += f"   - {cred.get('role', 'user')}: {cred.get('email', '')} / {cred.get('password', '')}\n"
                        else:
                            context += f"   - {cred}\n"
                context += "\n"

            # Handle project_info
            if 'project_info' in data:
                info = data['project_info']
                context += "## PROJECT INFO\n"
                context += f"   Frontend: {info.get('frontend_url', 'N/A')}\n"
                context += f"   Backend: {info.get('backend_url', 'N/A')}\n"
                context += "\n"

            # Handle generic routes format
            elif 'routes' in data:
                context += f"Total Routes: {len(data['routes'])}\n\n"
                for route in data['routes']:
                    methods = route.get('methods', ['GET'])
                    if isinstance(methods, list):
                        methods = '/'.join(methods)
                    path = route.get('path', route.get('endpoint', 'unknown'))
                    context += f"[{methods}] {path}\n"

            # If no recognized format, dump as JSON
            elif 'api_routes' not in data and 'routes' not in data:
                import json
                context += json.dumps(data, indent=2)
        else:
            context += str(data)

        context += "\n=== END API BLUEPRINT ===\n"
        return context

    def get_all_files_recursive(self, directory: str = ".") -> List[Dict]:
        """Recursively get all files in target directory."""
        files = []
        try:
            target_dir = TARGET_PROJECT_DIR / directory
            if not target_dir.exists():
                return files

            for item in target_dir.rglob("*"):
                if item.is_file() and item.suffix in ALLOWED_EXTENSIONS:
                    rel_path = str(item.relative_to(TARGET_PROJECT_DIR))
                    # Skip hidden files and common non-essential directories
                    if not any(part.startswith('.') for part in rel_path.split('/')):
                        if not any(skip in rel_path for skip in ['node_modules', '__pycache__', 'venv', '.git']):
                            files.append({
                                "path": rel_path,
                                "name": item.name,
                                "size": item.stat().st_size
                            })
            return files
        except Exception as e:
            logger.error(f"Error scanning files: {e}")
            return files

    def identify_relevant_files(self, task: str) -> List[str]:
        """Step 1: Ask Claude which files are relevant for the task."""
        import json
        import re

        try:
            # Get list of all files (names only, not content)
            all_files = self.get_all_files_recursive()
            if not all_files:
                return []

            file_list = "\n".join([f"- {f['path']} ({f['size']} bytes)" for f in all_files])

            prompt = f"""Given this task: "{task}"

Here are the available files in the project:
{file_list}

Which files are most relevant to complete this task? Return ONLY a JSON array of file paths, nothing else.
Example: ["src/index.js", "config.json"]

Be selective - only include files that are directly relevant to the task."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system="You are a helpful assistant that identifies relevant files for a task. Return only valid JSON arrays.",
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text.strip()
            # Parse JSON array from response
            json_match = re.search(r'\[.*?\]', result, re.DOTALL)
            if json_match:
                relevant_files = json.loads(json_match.group())
                logger.info(f"Claude identified {len(relevant_files)} relevant files for task")
                return relevant_files
            return []

        except Exception as e:
            logger.error(f"Error identifying relevant files: {e}")
            return []

    def process_task_two_step(self, task: str, project_id: int = None) -> Dict:
        """Two-step approach: identify relevant files, then process only those."""
        try:
            # Step 0: Fetch API blueprint for context
            logger.info("Step 0: Fetching target project API blueprint...")
            api_context = self.get_target_api_context(project_id)

            # Step 1: Identify relevant files
            logger.info(f"Step 1: Identifying relevant files for task: {task[:50]}...")
            relevant_files = self.identify_relevant_files(task)

            if not relevant_files:
                return {"error": "No relevant files found for this task"}

            # Step 2: Read only the relevant files
            logger.info(f"Step 2: Reading {len(relevant_files)} relevant files...")
            file_contents = {}
            total_size = 0

            for file_path in relevant_files:
                file_data = self.read_file(file_path)
                if "error" not in file_data:
                    file_contents[file_path] = file_data["content"]
                    total_size += len(file_data["content"])

            if not file_contents:
                return {"error": "Could not read any of the relevant files"}

            # Step 3: Send focused content to Claude with API context
            logger.info(f"Step 3: Sending {len(file_contents)} files ({total_size} chars) to Claude...")

            content_block = "\n\n".join([
                f"=== {path} ===\n{content}"
                for path, content in file_contents.items()
            ])

            # Include API blueprint in the prompt
            full_context = f"Task: {task}\n\n{api_context}\n\nRelevant files:\n\n{content_block}"

            self.conversation_history.append({
                "role": "user",
                "content": full_context
            })

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=self.conversation_history
            )

            assistant_response = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })

            # Record the analysis in database
            db.record_change(
                project_id=None,
                files_affected=list(file_contents.keys()),
                change_type="analyze",
                change_summary=task[:200],
                ai_response=assistant_response[:1000]
            )

            # Auto-save as finding if it looks like important analysis
            db.save_ai_context(
                content=assistant_response,
                context_type="finding",
                title=f"Analysis: {task[:50]}...",
                tags=["auto-generated", "task-analysis"]
            )

            return {
                "status": "success",
                "files_analyzed": list(file_contents.keys()),
                "total_files": len(file_contents),
                "total_chars": total_size,
                "response": assistant_response
            }

        except Exception as e:
            logger.error(f"Error in two-step process: {e}")
            return {"error": str(e)}
