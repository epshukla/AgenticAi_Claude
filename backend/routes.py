"""
Flask routes for the AI Agent API.
"""

import requests
from flask import Blueprint, request, jsonify, render_template, current_app, session
from . import database as db
from . import routes_generator
from .auth import login_user, logout_user, get_current_user, login_required
from .config import (
    DEMO_DIR,
    TARGET_PROJECT_DIR,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    CLAUDE_MODEL
)

# Create blueprint
api = Blueprint('api', __name__)


def get_agent():
    """Get the agent instance from the app context."""
    return current_app.config['AGENT']


# =============================================================================
# MAIN ROUTES
# =============================================================================

@api.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')


# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@api.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login endpoint."""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"error": "Username and password required", "success": False}), 400

    result = login_user(username, password)

    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 401


@api.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout endpoint."""
    result = logout_user()
    return jsonify(result)


@api.route('/api/auth/me', methods=['GET'])
def api_get_current_user():
    """Get current logged-in user."""
    user = get_current_user()
    if user:
        return jsonify({"user": user, "authenticated": True})
    else:
        return jsonify({"user": None, "authenticated": False})


# =============================================================================
# CHAT & TASK ROUTES
# =============================================================================

@api.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint - general conversation."""
    data = request.json
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    response = get_agent().chat(user_message, app=current_app)
    return jsonify({"response": response})


@api.route('/api/task', methods=['POST'])
def api_process_task():
    """Process a task using two-step approach (identify files, then analyze)."""
    data = request.json
    task = data.get('task', '').strip()

    if not task:
        return jsonify({"error": "Task description required"}), 400

    result = get_agent().process_task_two_step(task)
    return jsonify(result)


# =============================================================================
# FILE ROUTES
# =============================================================================

@api.route('/api/files', methods=['GET'])
def api_list_files():
    """List available files in target directory."""
    directory = request.args.get('directory', '.')
    return jsonify(get_agent().list_files(directory))


@api.route('/api/file/read', methods=['POST'])
def api_read_file():
    """Read a specific file."""
    data = request.json
    file_path = data.get('path', '').strip()

    if not file_path:
        return jsonify({"error": "File path required"}), 400

    return jsonify(get_agent().read_file(file_path))


@api.route('/api/file/modify', methods=['POST'])
def api_modify_file():
    """Modify a file using Claude."""
    data = request.json
    file_path = data.get('path', '').strip()
    instruction = data.get('instruction', '').strip()

    if not file_path or not instruction:
        return jsonify({"error": "File path and instruction required"}), 400

    result = get_agent().modify_file_with_claude(file_path, instruction)
    return jsonify(result)


# =============================================================================
# HISTORY & STATUS ROUTES
# =============================================================================

@api.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    """Clear conversation history."""
    get_agent().clear_history()
    return jsonify({"status": "Conversation history cleared"})


@api.route('/api/status', methods=['GET'])
def api_status():
    """Get agent status."""
    return jsonify({
        "status": "running",
        "model": CLAUDE_MODEL,
        "target_dir": str(TARGET_PROJECT_DIR),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "max_file_size": MAX_FILE_SIZE
    })


@api.route('/api/routes', methods=['GET'])
def api_list_routes():
    """List all available API routes - useful for agent self-awareness."""
    routes = []
    for rule in current_app.url_map.iter_rules():
        if not rule.endpoint.startswith('static'):
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods - {'HEAD', 'OPTIONS'}),
                "path": rule.rule
            })
    return jsonify({
        "routes": routes,
        "description": "Available API endpoints for the AI agent"
    })


@api.route('/api/routes/info', methods=['GET'])
def api_routes_info():
    """Get comprehensive routes information including frontend URLs."""
    info = routes_generator.get_all_routes_info(current_app)
    return jsonify(info)


@api.route('/api/routes/export', methods=['POST'])
def api_export_routes():
    """Export routes documentation to markdown file."""
    data = request.json or {}
    filepath = data.get('filepath') or str(DEMO_DIR / "app_routes.md")

    try:
        routes_generator.generate_routes_markdown(current_app, filepath)
        return jsonify({
            "status": "success",
            "filepath": filepath,
            "message": "Routes documentation exported successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =============================================================================
# TARGET PROJECT PROXY ROUTES
# =============================================================================

def get_target_backend_url(project_id: int = None) -> str:
    """Get the backend URL for a project."""
    if project_id:
        project = db.get_project_by_id(project_id)
        if project and project.get('backend_url'):
            return project['backend_url']
    # Default fallback
    projects = db.get_projects()
    if projects and projects[0].get('backend_url'):
        return projects[0]['backend_url']
    return "http://localhost:5001"


@api.route('/api/target/blueprint', methods=['GET'])
def api_target_blueprint():
    """Fetch blueprint from target project."""
    project_id = request.args.get('project_id', type=int)
    backend_url = get_target_backend_url(project_id)

    try:
        response = requests.get(f"{backend_url}/api/blueprint", timeout=10)
        if response.status_code != 200:
            return jsonify({"error": f"Target returned status {response.status_code}", "raw": response.text[:500]}), response.status_code
        try:
            return jsonify(response.json())
        except ValueError:
            return jsonify({"error": "Target returned non-JSON response", "raw": response.text[:500]}), 502
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Cannot connect to target project at {backend_url}. Is it running?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to target project timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/target/blueprint_json', methods=['GET'])
def api_target_blueprint_json():
    """Fetch blueprint JSON from target project."""
    project_id = request.args.get('project_id', type=int)
    backend_url = get_target_backend_url(project_id)

    try:
        response = requests.get(f"{backend_url}/api/blueprint_json", timeout=10)
        if response.status_code != 200:
            return jsonify({"error": f"Target returned status {response.status_code}", "raw": response.text[:500]}), response.status_code
        try:
            return jsonify(response.json())
        except ValueError:
            return jsonify({"error": "Target returned non-JSON response", "raw": response.text[:500]}), 502
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Cannot connect to target project at {backend_url}. Is it running?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to target project timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/target/proxy', methods=['GET', 'POST'])
def api_target_proxy():
    """Generic proxy to target project API."""
    project_id = request.args.get('project_id', type=int)
    endpoint = request.args.get('endpoint', '')
    backend_url = get_target_backend_url(project_id)

    if not endpoint:
        return jsonify({"error": "endpoint parameter required"}), 400

    # Ensure endpoint starts with /
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint

    try:
        if request.method == 'GET':
            response = requests.get(f"{backend_url}{endpoint}", timeout=10)
        else:
            response = requests.post(
                f"{backend_url}{endpoint}",
                json=request.json,
                timeout=10
            )
        if response.status_code != 200:
            return jsonify({"error": f"Target returned status {response.status_code}", "raw": response.text[:500]}), response.status_code
        try:
            return jsonify(response.json())
        except ValueError:
            return jsonify({"error": "Target returned non-JSON response", "raw": response.text[:500]}), 502
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Cannot connect to target project at {backend_url}. Is it running?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to target project timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/api/target/ai-context', methods=['GET'])
def api_target_ai_context():
    """Get the API context that AI uses for analysis."""
    project_id = request.args.get('project_id', type=int)
    agent = get_agent()

    # Get raw blueprint
    blueprint = agent.fetch_target_blueprint(project_id)

    # Get formatted context
    formatted_context = agent.get_target_api_context(project_id)

    return jsonify({
        "blueprint": blueprint,
        "formatted_context": formatted_context,
        "status": "success" if not blueprint.get('error') else "error"
    })


# =============================================================================
# USER ROUTES
# =============================================================================

@api.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users."""
    return jsonify({"users": db.get_users()})


@api.route('/api/users', methods=['POST'])
def api_create_user():
    """Create a new user."""
    data = request.json
    username = data.get('username', '').strip()
    role = data.get('role', '').strip()
    email = data.get('email', '').strip() or None

    if not username or role not in ('admin', 'tester', 'developer'):
        return jsonify({"error": "Valid username and role (admin/tester/developer) required"}), 400

    try:
        user_id = db.create_user(username, role, email)
        return jsonify({"status": "success", "user_id": user_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =============================================================================
# PROJECT ROUTES
# =============================================================================

@api.route('/api/projects', methods=['GET'])
def api_get_projects():
    """Get all projects."""
    return jsonify({"projects": db.get_projects()})


@api.route('/api/projects', methods=['POST'])
def api_create_project():
    """Create a new project."""
    data = request.json
    title = data.get('title', '').strip()
    path = data.get('path', '').strip()
    description = data.get('description', '').strip() or None

    if not title or not path:
        return jsonify({"error": "Title and path required"}), 400

    project_id = db.create_project(title, path, description)
    return jsonify({"status": "success", "project_id": project_id})


# =============================================================================
# TICKET ROUTES
# =============================================================================

@api.route('/api/tickets', methods=['GET'])
def api_get_tickets():
    """Get tickets with optional filters."""
    project_id = request.args.get('project_id', type=int)
    status = request.args.get('status')
    return jsonify({"tickets": db.get_tickets(project_id, status)})


@api.route('/api/tickets', methods=['POST'])
def api_create_ticket():
    """Create a new ticket."""
    data = request.json
    title = data.get('title', '').strip()
    category = data.get('category', '').strip()

    if not title or category not in ('bug', 'feature', 'task', 'improvement'):
        return jsonify({"error": "Title and valid category required"}), 400

    ticket_id = db.create_ticket(
        title=title,
        category=category,
        description=data.get('description'),
        creator_id=data.get('creator_id'),
        project_id=data.get('project_id'),
        priority=data.get('priority', 'medium')
    )
    return jsonify({"status": "success", "ticket_id": ticket_id})


@api.route('/api/tickets/<int:ticket_id>/status', methods=['PUT'])
def api_update_ticket_status(ticket_id):
    """Update ticket status."""
    data = request.json
    status = data.get('status', '').strip()

    if status not in ('open', 'in_progress', 'resolved', 'closed'):
        return jsonify({"error": "Invalid status"}), 400

    success = db.update_ticket_status(ticket_id, status)
    return jsonify({"status": "success" if success else "not_found"})


@api.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def api_get_ticket(ticket_id):
    """Get a single ticket with full details."""
    ticket = db.get_ticket_by_id(ticket_id)
    if ticket:
        return jsonify({"ticket": ticket})
    else:
        return jsonify({"error": "Ticket not found"}), 404


@api.route('/api/tickets/<int:ticket_id>/ai-resolve', methods=['POST'])
def api_ticket_ai_resolve(ticket_id):
    """Trigger AI resolution for a ticket."""
    ticket = db.get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    # Get project info for API context
    project_id = ticket.get('project_id')
    project_info = ""
    if project_id:
        project = db.get_project_by_id(project_id)
        if project:
            project_info = f"""
Project: {project.get('title', 'Unknown')}
Frontend URL: {project.get('frontend_url', 'N/A')}
Backend URL: {project.get('backend_url', 'N/A')}
"""

    # Build task description from ticket
    task = f"""Analyze and resolve this ticket:
{project_info}
Title: {ticket['title']}
Category: {ticket['category']}
Priority: {ticket['priority']}
Description: {ticket.get('description') or 'No description provided'}

Please:
1. Identify the relevant files in the codebase
2. Analyze the issue (use the API blueprint info if relevant)
3. Provide a detailed resolution or implementation plan
4. If it's a bug, explain the root cause and fix
5. If it's a feature/task, provide implementation steps
6. Reference specific API endpoints if the issue involves the API
7. IMPORTANT: At the end, list the files that need to be modified in this format:
   FILES_TO_MODIFY:
   - path/to/file1.py: description of changes needed
   - path/to/file2.js: description of changes needed"""

    # Use the agent's two-step process with project context
    agent = get_agent()
    result = agent.process_task_two_step(task, project_id=project_id)

    if result.get('error'):
        return jsonify(result), 400

    # Store the AI suggestion in the ticket
    ai_response = result.get('response', '')
    files_analyzed = result.get('files_analyzed', [])

    db.update_ticket_ai_suggestion(
        ticket_id,
        ai_response,
        files_analyzed
    )

    # Auto-generate proposed changes for files that need modification
    proposed_changes = []
    if 'FILES_TO_MODIFY:' in ai_response:
        # Parse the files to modify section
        lines = ai_response.split('FILES_TO_MODIFY:')[-1].strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- ') and ':' in line:
                parts = line[2:].split(':', 1)
                file_path = parts[0].strip()
                instruction = parts[1].strip() if len(parts) > 1 else f"Apply fix for: {ticket['title']}"

                # Generate proposed change for this file
                if file_path in files_analyzed:
                    change_result = agent.propose_file_change(
                        file_path,
                        f"{ticket['title']}: {instruction}",
                        ticket_id
                    )
                    if change_result.get('status') == 'proposed':
                        proposed_changes.append({
                            'file': file_path,
                            'change_id': change_result.get('change_id')
                        })

    return jsonify({
        "status": "success",
        "suggestion": ai_response,
        "files_analyzed": files_analyzed,
        "proposed_changes": proposed_changes
    })


@api.route('/api/tickets/<int:ticket_id>/ai-action', methods=['POST'])
def api_ticket_ai_action(ticket_id):
    """Accept, reject, or probe more on AI suggestion."""
    data = request.json
    action = data.get('action', '').strip()

    if action not in ('accept', 'reject', 'probe'):
        return jsonify({"error": "Invalid action. Use: accept, reject, or probe"}), 400

    ticket = db.get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    agent = get_agent()

    if action == 'accept':
        # Apply all pending proposed changes for this ticket
        pending_changes = db.get_proposed_changes_for_ticket(ticket_id)
        applied_changes = []

        for change in pending_changes:
            if change['status'] == 'pending':
                result = agent.apply_proposed_change(change['id'])
                if result.get('status') == 'applied':
                    applied_changes.append(change['file_path'])

        db.update_ticket_ai_status(ticket_id, 'accepted')

        return jsonify({
            "status": "success",
            "message": "AI suggestion accepted, ticket resolved",
            "applied_changes": applied_changes
        })

    elif action == 'reject':
        # Reject all pending proposed changes for this ticket
        pending_changes = db.get_proposed_changes_for_ticket(ticket_id)
        for change in pending_changes:
            if change['status'] == 'pending':
                agent.reject_proposed_change(change['id'])

        db.update_ticket_ai_status(ticket_id, 'rejected')
        return jsonify({"status": "success", "message": "AI suggestion rejected"})

    elif action == 'probe':
        # Probe more - use the chat to ask follow-up
        message = data.get('message', '').strip()
        if not message:
            return jsonify({"error": "Message required for probe action"}), 400

        # Build context from ticket and previous suggestion
        context = f"""Continuing analysis of ticket #{ticket_id}:
Title: {ticket['title']}
Category: {ticket['category']}
Previous AI suggestion: {ticket.get('ai_suggestion', 'None')}

User's follow-up question: {message}"""

        response = agent.chat(context, app=current_app)

        return jsonify({
            "status": "success",
            "response": response
        })


@api.route('/api/tickets/<int:ticket_id>/chat', methods=['POST'])
def api_ticket_chat(ticket_id):
    """Chat about a specific ticket."""
    data = request.json
    message = data.get('message', '').strip()

    if not message:
        return jsonify({"error": "Message required"}), 400

    ticket = db.get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    # Build context
    context = f"""Discussing ticket #{ticket_id}:
Title: {ticket['title']}
Category: {ticket['category']}
Priority: {ticket['priority']}
Status: {ticket['status']}
Description: {ticket.get('description') or 'None'}
AI Suggestion: {ticket.get('ai_suggestion') or 'None'}

User message: {message}"""

    agent = get_agent()
    response = agent.chat(context, app=current_app)

    return jsonify({
        "status": "success",
        "response": response
    })


# =============================================================================
# PROPOSED CHANGES ROUTES
# =============================================================================

@api.route('/api/proposed-changes', methods=['GET'])
def api_get_proposed_changes():
    """Get all pending proposed changes."""
    changes = db.get_pending_proposed_changes()
    return jsonify({"changes": changes})


@api.route('/api/proposed-changes/<int:change_id>', methods=['GET'])
def api_get_proposed_change(change_id):
    """Get a specific proposed change."""
    change = db.get_proposed_change(change_id)
    if not change:
        return jsonify({"error": "Proposed change not found"}), 404
    return jsonify({"change": change})


@api.route('/api/tickets/<int:ticket_id>/proposed-changes', methods=['GET'])
def api_get_ticket_proposed_changes(ticket_id):
    """Get all proposed changes for a ticket."""
    changes = db.get_proposed_changes_for_ticket(ticket_id)
    return jsonify({"changes": changes})


@api.route('/api/tickets/<int:ticket_id>/propose-change', methods=['POST'])
def api_propose_change(ticket_id):
    """Propose a file change for a ticket."""
    data = request.json
    file_path = data.get('file_path', '').strip()
    instruction = data.get('instruction', '').strip()

    if not file_path or not instruction:
        return jsonify({"error": "file_path and instruction required"}), 400

    ticket = db.get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    agent = get_agent()
    result = agent.propose_file_change(file_path, instruction, ticket_id)

    if result.get('error'):
        return jsonify(result), 400

    return jsonify(result)


@api.route('/api/proposed-changes/<int:change_id>/accept', methods=['POST'])
def api_accept_proposed_change(change_id):
    """Accept and apply a proposed change."""
    agent = get_agent()
    result = agent.apply_proposed_change(change_id)

    if result.get('error'):
        return jsonify(result), 400

    return jsonify(result)


@api.route('/api/proposed-changes/<int:change_id>/reject', methods=['POST'])
def api_reject_proposed_change(change_id):
    """Reject a proposed change."""
    agent = get_agent()
    result = agent.reject_proposed_change(change_id)

    if result.get('error'):
        return jsonify(result), 400

    return jsonify(result)


# =============================================================================
# CHANGES HISTORY ROUTES
# =============================================================================

@api.route('/api/changes', methods=['GET'])
def api_get_changes():
    """Get changes history."""
    project_id = request.args.get('project_id', type=int)
    limit = request.args.get('limit', 50, type=int)
    return jsonify({"changes": db.get_changes_history(project_id, limit)})


# =============================================================================
# AI CONTEXT ROUTES
# =============================================================================

@api.route('/api/context', methods=['GET'])
def api_get_context():
    """Get AI context entries."""
    project_id = request.args.get('project_id', type=int)
    context_type = request.args.get('type')
    return jsonify({"context": db.get_ai_context(project_id, context_type)})


@api.route('/api/context', methods=['POST'])
def api_save_context():
    """Save an AI context/finding."""
    data = request.json
    content = data.get('content', '').strip()

    if not content:
        return jsonify({"error": "Content required"}), 400

    context_id = db.save_ai_context(
        content=content,
        context_type=data.get('type', 'finding'),
        title=data.get('title'),
        project_id=data.get('project_id'),
        tags=data.get('tags')
    )
    return jsonify({"status": "success", "context_id": context_id})


@api.route('/api/context/export', methods=['POST'])
def api_export_context():
    """Export AI context to markdown file."""
    data = request.json or {}
    filepath = data.get('filepath') or str(DEMO_DIR / "agentic_ai_context.md")

    try:
        result_path = db.export_ai_context_to_file(filepath, data.get('project_id'))
        return jsonify({"status": "success", "filepath": result_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
