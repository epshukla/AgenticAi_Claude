# Claude Chatbot Agent with UI

A modern web-based chatbot interface that leverages Claude AI to intelligently read and modify files across different project directories. This application provides a user-friendly chat interface combined with powerful file management capabilities.

## 🎯 Features

- **💬 Interactive Chat Interface**: Real-time conversation with Claude AI
- **📁 File Browser**: Browse and select files from target directories
- **📄 File Preview**: View file contents before modification
- **✨ Intelligent File Modification**: Ask Claude to modify files with natural language instructions
- **🔒 Enterprise Security**: Multi-layer safety checks and validation
- **📊 Conversation History**: Maintains context across multiple interactions
- **📝 Audit Logging**: All operations are logged for transparency

## 📋 Architecture

```
demo/
├── ui_agent.py          # Flask backend with Claude integration
├── config.py            # Configuration and safety policies
├── templates/
│   └── index.html       # Web UI (chat + file browser)
├── requirements.txt     # Python dependencies
└── agent.log           # Operation audit log

demo2/
└── README.md           # Target project files (editable by agent)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/theperson/Vajra/MyProjects/CyberCypher26/demo
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Set your Claude API key
export CLAUDE_API_KEY="your-api-key-here"
```

Or update the `config.py` file directly with your API key.

### 3. Run the Application

```bash
python ui_agent.py
```

The application will start on `http://localhost:5000`

### 4. Open in Browser

Navigate to: **http://localhost:5000**

## 📖 Usage Guide

### Chat Interface

1. **Select a File**: Click on any file in the left sidebar to preview its contents
2. **Chat with Claude**: Type a message in the chat input and click "Send Chat"
3. **Modify Files**: Enter an instruction (e.g., "Improve this README") and click "Modify File"

### Examples of Instructions

- "Improve the documentation and make it more professional"
- "Add more examples to this code"
- "Fix any spelling or grammar errors"
- "Reorganize this content for better clarity"
- "Add a table of contents at the beginning"

## 🔐 Security Architecture

### Multi-Layer Validation

1. **Path Validation**: All file paths are validated to ensure they stay within `TARGET_PROJECT_DIR`
2. **Extension Whitelist**: Only specific file types can be accessed (.md, .txt, .json, .py, etc.)
3. **File Size Limits**: Files larger than 100 KB are rejected
4. **Existence Checks**: Files must exist before reading or modification

### Claude Isolation

- Claude **never** receives file paths or filesystem information
- Claude only sees file **content** and instructions
- All file I/O operations are controlled by the Python agent
- Claude cannot execute commands or access the filesystem

## 📡 API Endpoints

### Chat Endpoint
```
POST /api/chat
Body: { "message": "Your message here" }
Response: { "response": "Claude's response" }
```

### List Files
```
GET /api/files?directory=.
Response: { "files": [...], "directory": "." }
```

### Read File
```
POST /api/file/read
Body: { "path": "relative/path/to/file.md" }
Response: { "path": "...", "content": "...", "size": 1234, "extension": ".md" }
```

### Modify File
```
POST /api/file/modify
Body: { "path": "relative/path/to/file.md", "instruction": "Improve this" }
Response: { "status": "success", "path": "...", "original_size": 1000, "modified_size": 1500 }
```

### Clear History
```
POST /api/history/clear
Response: { "status": "Conversation history cleared" }
```

### Status
```
GET /api/status
Response: { "status": "running", "model": "claude-opus-4-1-20250805", ... }
```

## 🛠️ Configuration

Edit `config.py` to customize:

```python
# Target directory containing files to modify
TARGET_PROJECT_DIR = Path("/path/to/demo2").absolute()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".py"}

# Maximum file size
MAX_FILE_SIZE = 100 * 1024  # 100 KB

# Claude model
CLAUDE_MODEL = "claude-opus-4-1-20250805"

# System prompt for Claude
SYSTEM_PROMPT = """Your custom instructions here"""
```

## 📊 Logs

All operations are logged to `agent.log`:

```
2025-02-01 10:30:45 - UIAgent - INFO - File read successfully: README.md
2025-02-01 10:31:20 - UIAgent - INFO - Sending file to Claude with instruction: Improve this
2025-02-01 10:31:45 - UIAgent - INFO - File modified and saved: README.md
```

## 🐛 Troubleshooting

### "CLAUDE_API_KEY not found"
- Set the environment variable: `export CLAUDE_API_KEY="your-key"`
- Or update it directly in `config.py`

### Port 5000 already in use
- Change the port in `ui_agent.py`: `app.run(port=5001)`

### Files not appearing
- Ensure files are in the `TARGET_PROJECT_DIR` (demo2/)
- Check that file extensions are in `ALLOWED_EXTENSIONS`
- Check file size doesn't exceed `MAX_FILE_SIZE`

### Claude API errors
- Verify your API key is correct
- Check your Claude API account has available credits
- Ensure you're using a valid model name

## 📦 Dependencies

- **Flask**: Web framework for the UI
- **Anthropic**: Official Claude API client
- **Flask-CORS**: Handle cross-origin requests
- **python-dotenv**: Load environment variables

## 🎓 How It Works

### File Modification Flow

```
1. User selects file in UI
2. Backend reads file from disk
3. File content sent to Claude (path NOT exposed)
4. Claude processes with user's instruction
5. Modified content returned by Claude
6. Backend validates the result
7. Backend writes to disk
8. UI refreshed with new content
```

### Conversation Management

- Maintains conversation history within a session
- Claude can reference previous messages
- History cleared on command or app restart
- Each session is isolated for privacy

## 🔄 Advanced Usage

### Batch Operations

Send multiple modification instructions in sequence:

1. Select a file
2. Send instruction: "Improve formatting"
3. Send instruction: "Add examples"
4. Send instruction: "Create a summary"

Claude maintains context and applies changes cumulatively.

### Multi-File Workflows

1. Modify file A with specific instruction
2. View file B
3. Modify file B referencing changes from file A
4. Continue building related content

## 📝 Notes

- Each conversation maintains context. Use "Clear" to reset
- File modifications are atomic (all-or-nothing)
- Large files (>100KB) are rejected for safety
- All operations are logged for audit purposes
- The agent runs with the permissions of the current user

## 🚀 Production Deployment

For production use:

1. Set `debug=False` in `ui_agent.py`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Store API keys in secure environment variables
4. Set up proper logging and monitoring
5. Use HTTPS/SSL certificates
6. Implement authentication/authorization
7. Set up regular backups

### Example Gunicorn Command

```bash
gunicorn -w 4 -b 0.0.0.0:8000 ui_agent:app
```

## 📄 License

This project is part of the CyberCypher26 suite.

## 🤝 Support

For issues or questions, check the logs in `agent.log` or review the ARCHITECTURE.md for deeper technical details.

---

**Happy coding! 🚀**
