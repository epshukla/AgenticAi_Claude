#!/usr/bin/env python3
"""
Claude Chatbot Agent with Web UI

This is a Flask-based web application that provides a user-friendly chatbot interface
for interacting with Claude AI. The chatbot can read and modify files across different
directories with full security validation.

Features:
- Real-time chat interface
- File browser and selection
- Safe file modification with Claude
- Audit logging of all operations
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import anthropic

from config import (
    DEMO_DIR,
    TARGET_PROJECT_DIR,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    SYSTEM_PROMPT,
    validate_target_path
)

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DEMO_DIR / "agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__, template_folder=str(DEMO_DIR / "templates"))
CORS(app)

# ============================================================================
# CLAUDE AI AGENT CLASS
# ============================================================================

class UIAgent:
    """Agent that handles file operations and Claude interactions via web interface."""
    
    def __init__(self, api_key: str, model: str = CLAUDE_MODEL):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history = []
        logger.info("UIAgent initialized")
    
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
                        "modified": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).isoformat()
                    })
            
            logger.info(f"Listed {len(files)} files in {directory}")
            return {"files": files, "directory": directory}
        
        except Exception as e:
            logger.error(f"Error listing files: {e}")
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
    
    def chat(self, user_message: str) -> str:
        """Send a message to Claude and get a response."""
        try:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system="You are a helpful AI assistant that helps users manage files and content. Be concise and helpful.",
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            logger.info(f"Chat response generated")
            return assistant_message
        
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

# ============================================================================
# INITIALIZE AGENT
# ============================================================================

agent = UIAgent(CLAUDE_API_KEY)

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint - general conversation."""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    response = agent.chat(user_message)
    return jsonify({"response": response})

@app.route('/api/files', methods=['GET'])
def api_list_files():
    """List available files in target directory."""
    directory = request.args.get('directory', '.')
    return jsonify(agent.list_files(directory))

@app.route('/api/file/read', methods=['POST'])
def api_read_file():
    """Read a specific file."""
    data = request.json
    file_path = data.get('path', '').strip()
    
    if not file_path:
        return jsonify({"error": "File path required"}), 400
    
    return jsonify(agent.read_file(file_path))

@app.route('/api/file/modify', methods=['POST'])
def api_modify_file():
    """Modify a file using Claude."""
    data = request.json
    file_path = data.get('path', '').strip()
    instruction = data.get('instruction', '').strip()
    
    if not file_path or not instruction:
        return jsonify({"error": "File path and instruction required"}), 400
    
    result = agent.modify_file_with_claude(file_path, instruction)
    return jsonify(result)

@app.route('/api/history/clear', methods=['POST'])
def api_clear_history():
    """Clear conversation history."""
    agent.clear_history()
    return jsonify({"status": "Conversation history cleared"})

@app.route('/api/status', methods=['GET'])
def api_status():
    """Get agent status."""
    return jsonify({
        "status": "running",
        "model": CLAUDE_MODEL,
        "target_dir": str(TARGET_PROJECT_DIR),
        "allowed_extensions": list(ALLOWED_EXTENSIONS),
        "max_file_size": MAX_FILE_SIZE
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting Claude Chatbot UI Agent")
    logger.info(f"Target directory: {TARGET_PROJECT_DIR}")
    logger.info(f"Allowed extensions: {ALLOWED_EXTENSIONS}")
    
    # Create templates directory if it doesn't exist
    templates_dir = DEMO_DIR / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
