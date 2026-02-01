# 🚀 Claude Chatbot UI - Quick Reference

## Get Started in 3 Steps

```bash
# 1. Go to demo directory
cd /home/theperson/Vajra/MyProjects/CyberCypher26/demo

# 2. Run the startup script
chmod +x start.sh && ./start.sh

# 3. Open in browser
# http://localhost:5000
```

---

## Main Features at a Glance

| Feature | How to Use | Example |
|---------|-----------|---------|
| **Chat** | Type message → Click "Send Chat" | "What's in this file?" |
| **Browse Files** | Click file in left sidebar | Select README.md |
| **Preview** | File appears on right panel | View content before modifying |
| **Modify File** | Enter instruction → Click "Modify File" | "Improve this documentation" |
| **Clear History** | Click "Clear" button | Reset conversation context |

---

## What Each Panel Does

```
┌─────────────────────────────────────────────────────────┐
│  LEFT          │        CENTER           │     RIGHT    │
│                │                         │              │
│ 📁 Files       │  💬 Chat Messages       │  📄 Preview  │
│                │  ✨ Instructions        │              │
│ • README.md    │  📝 Modify File Button  │  File        │
│ • config.json  │  💬 Send Chat Button    │  Contents    │
│ • ...          │  🔄 Clear Button        │  Here        │
│                │                         │              │
└─────────────────────────────────────────────────────────┘
```

---

## Common Use Cases

### 1. Improve Documentation
```
1. Click README.md in left panel
2. Type: "Make this README more professional and comprehensive"
3. Click "Modify File"
4. See updated content in preview
```

### 2. Fix Code Issues
```
1. Select a Python file
2. Type: "Fix any syntax errors and improve code style"
3. Click "Modify File"
4. File updated automatically
```

### 3. Add Examples
```
1. Select a file
2. Type: "Add 3 practical examples to this content"
3. Click "Modify File"
4. Enhanced with examples
```

### 4. Ask Questions
```
1. Select any file
2. Type: "What's the main purpose of this?"
3. Click "Send Chat"
4. Claude explains the content
```

---

## Configuration

Edit `config.py` to change:

```python
# Change where files are stored
TARGET_PROJECT_DIR = Path("/your/target/directory")

# Add allowed file types
ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".py"}

# Increase file size limit
MAX_FILE_SIZE = 500 * 1024  # 500 KB instead of 100 KB

# Set API key
CLAUDE_API_KEY = "your-key-here"
```

---

## Example Instructions for Claude

📝 **Documentation**
- "Make this README more comprehensive"
- "Fix any spelling and grammar errors"
- "Add a table of contents"
- "Create a quick start section"
- "Make this more beginner-friendly"

🐍 **Code**
- "Improve the readability of this code"
- "Add comments explaining what this does"
- "Follow PEP-8 style guidelines"
- "Add error handling"
- "Optimize this for performance"

📊 **Content**
- "Reorganize for better flow"
- "Create bullet points instead of paragraphs"
- "Add a summary section"
- "Include real-world examples"
- "Make it more concise"

---

## File Operations Flow

```
SELECT FILE
    ↓
PREVIEW CONTENT
    ↓
ENTER INSTRUCTION
    ↓
CLICK "MODIFY FILE"
    ↓
Claude processes...
    ↓
FILE UPDATED
    ↓
PREVIEW REFRESHES
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Server won't start | Check port 5000 not in use, or change in ui_agent.py |
| API key error | Set: `export CLAUDE_API_KEY="your-key"` |
| Files not showing | Ensure they're in demo2 and have allowed extensions |
| File too large | Max 100 KB, change MAX_FILE_SIZE in config.py |
| Permission denied | Use `chmod +x start.sh` and check file permissions |

---

## Environment Setup

```bash
# Set API key (if not in config.py)
export CLAUDE_API_KEY="sk-ant-..."

# Or set in config.py directly
CLAUDE_API_KEY = "sk-ant-..."
```

---

## Browser Access

```
http://localhost:5000/
```

Once running, you'll see:
- Left panel: File list
- Center: Chat interface
- Right panel: File preview

---

## Stop the Server

Press **Ctrl+C** in terminal

---

## Reset Everything

```bash
# Stop the server (Ctrl+C)

# Clear conversation history
# Click "Clear" button in UI

# Remove logs
rm agent.log

# Start fresh
./start.sh
```

---

## API Endpoints (Advanced)

For direct API use:

```bash
# Chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'

# List files
curl http://localhost:5000/api/files

# Read file
curl -X POST http://localhost:5000/api/file/read \
  -H "Content-Type: application/json" \
  -d '{"path":"README.md"}'

# Modify file
curl -X POST http://localhost:5000/api/file/modify \
  -H "Content-Type: application/json" \
  -d '{"path":"README.md","instruction":"Improve this"}'
```

---

## Key Files

```
demo/
├── ui_agent.py          ← Main server (START HERE)
├── config.py            ← Settings (CONFIGURE HERE)
├── requirements.txt     ← Dependencies
├── start.sh             ← Quick start script
├── UI_README.md         ← Full documentation
├── CHATBOT_SUMMARY.md   ← Detailed guide
└── templates/
    └── index.html       ← Web UI
```

---

## Quick Commands

```bash
# Start server
./start.sh

# Or manually:
source .venv/bin/activate
python3 ui_agent.py

# Check logs
tail -f agent.log

# Install deps
pip install -r requirements.txt
```

---

## What's New vs Original Agent

| Aspect | Original (agent.py) | New (ui_agent.py) |
|--------|-------------------|-------------------|
| Interface | Command line | Web UI |
| Interaction | Script-based | Interactive chat |
| File ops | Predefined | User-controlled |
| History | N/A | Full conversation history |
| File preview | N/A | Real-time preview |
| Ease of use | Developer | Anyone |

---

## Architecture in One Diagram

```
Browser
   ↓
HTML/CSS/JS (index.html)
   ↓
Flask REST API (ui_agent.py)
   ↓ ┌─────────────────────────┐
   ├→ Claude API
   ├→ File System (demo2/)
   └→ Logging (agent.log)
```

---

## Remember

✅ Always backup files before modifying  
✅ Test with small files first  
✅ Check logs if something fails  
✅ Use clear, specific instructions  
✅ Claude maintains context in conversation  

---

**Questions? Check UI_README.md or CHATBOT_SUMMARY.md** 📖
