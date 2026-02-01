# AI Context Efficiency Techniques

This document outlines the techniques used in this AI Agent to minimize token usage and make Claude API requests more efficient, rather than sending entire codebases with each request.

---

## 1. Blueprint Route from Target Project

Instead of parsing source code files to understand the target project's API structure, we fetch a pre-built summary from the target project itself.

### How It Works

The target project exposes a `/api/blueprint` or `/api/blueprint_json` endpoint that returns a structured summary of:
- All API routes and their methods
- Route groupings and prefixes
- Test credentials
- Project URLs (frontend/backend)

### Implementation

```python
# agent.py - fetch_target_blueprint()
def fetch_target_blueprint(self, project_id: int = None) -> Dict:
    """Fetch blueprint from target project's API."""
    backend_url = project['backend_url']

    # Try blueprint endpoints
    for endpoint in ['/api/blueprint_json', '/api/blueprint']:
        response = requests.get(f"{backend_url}{endpoint}", timeout=5)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
```

### Token Savings

| Approach | Tokens Used |
|----------|-------------|
| Parsing all route files | ~10,000-50,000 tokens |
| Blueprint endpoint | ~500-2,000 tokens |

**Savings: 80-95%**

---

## 2. Two-Step File Processing

Instead of sending all project files to Claude, we use a two-step approach to identify and send only relevant files.

### How It Works

**Step 1: File Identification (Lightweight)**
- Send Claude a list of file names only (not content)
- Ask which files are relevant to the task
- Uses `max_tokens=1024` (small response)

**Step 2: Selective Reading**
- Read only the files Claude identified
- Send those file contents for analysis
- Uses `max_tokens=4096` (full analysis)

### Implementation

```python
# agent.py - process_task_two_step()
def process_task_two_step(self, task: str, project_id: int = None) -> Dict:
    # Step 1: Identify relevant files (lightweight call)
    relevant_files = self.identify_relevant_files(task)  # max_tokens=1024

    # Step 2: Read only those files
    for file_path in relevant_files:
        file_data = self.read_file(file_path)
        file_contents[file_path] = file_data["content"]

    # Step 3: Send focused content to Claude
    full_context = f"Task: {task}\n\n{api_context}\n\nRelevant files:\n\n{content_block}"
```

### Token Savings

For a project with 100 files (~500KB total):

| Approach | Files Sent | Tokens Used |
|----------|------------|-------------|
| Send all files | 100 | ~150,000 tokens |
| Two-step (avg 5 relevant) | 5 | ~15,000 tokens |

**Savings: 70-90%**

---

## 3. Keyword-Based Context Inclusion

Route and API context is only added to prompts when the user's message indicates they need it.

### How It Works

```python
# agent.py - chat()
route_keywords = ['route', 'endpoint', 'api', 'url', 'path', 'navigate']
if any(kw in user_message.lower() for kw in route_keywords):
    routes_context = f"\n\nTarget Project Routes:\n{self.get_target_routes_context(app)}"
```

### Token Savings

- Route context: ~1,000-3,000 tokens
- Only included when relevant
- General chat queries skip this entirely

---

## 4. File Filtering and Exclusions

Unnecessary files are filtered out before any processing.

### Exclusions

```python
# config.py
ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".py",
                      ".config", ".html", ".css", ".js", ".jsx", ".ts", ".tsx"}
MAX_FILE_SIZE = 100 * 1024  # 100 KB limit

# agent.py - get_all_files_recursive()
skip_dirs = ['node_modules', '__pycache__', 'venv', '.git']
```

### What Gets Filtered

| Filtered Out | Reason |
|--------------|--------|
| `node_modules/` | Dependencies, not project code |
| `__pycache__/` | Compiled Python files |
| `venv/`, `.venv/` | Virtual environment |
| `.git/` | Version control |
| Binary files | Not text-parseable |
| Files > 100KB | Likely generated/data files |

---

## 5. Granular Token Allocation

Different operations use different `max_tokens` based on expected response size.

```python
# File identification (just need a list)
max_tokens=1024

# Chat responses (conversational)
max_tokens=2048

# File modification (need full code)
max_tokens=4096
```

---

## 6. Structured API Context Formatting

Raw JSON from blueprints is formatted into a compact, readable format.

### Before (Raw JSON)
```json
{
  "api_routes": {
    "auth": {
      "prefix": "/api/auth",
      "file": "routes/auth.py",
      "endpoints": ["POST /login", "POST /register"]
    }
  }
}
```

### After (Formatted for AI)
```
## AUTH (/api/auth)
   File: routes/auth.py
   - POST /login
   - POST /register
```

**Reduction: ~30% fewer tokens**

---

## Summary

| Technique | Token Savings |
|-----------|---------------|
| Blueprint endpoint | 80-95% |
| Two-step file selection | 70-90% |
| Keyword-based context | Variable (0-3K tokens) |
| File filtering | Prevents wasted tokens |
| Granular max_tokens | Right-sized responses |
| Structured formatting | ~30% reduction |

These techniques combined allow the AI agent to work with large codebases efficiently without hitting token limits or incurring unnecessary API costs.
