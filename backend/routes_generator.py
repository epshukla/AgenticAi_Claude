"""
Routes Generator Module

Scans the TARGET PROJECT for routes/endpoints and generates documentation.
Supports: Flask, Express, FastAPI, Django, and generic pattern matching.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import DEMO_DIR, TARGET_PROJECT_DIR, ALLOWED_EXTENSIONS


# AI Agent URLs (this app)
AGENT_URLS = {
    "backend": "http://localhost:8080",
    "frontend": "http://localhost:4000"
}


def scan_flask_routes(content: str, filepath: str) -> List[Dict]:
    """Scan Python file for Flask routes."""
    routes = []
    # Match @app.route, @blueprint.route, @api.route etc.
    pattern = r'@\w+\.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?\)'

    for match in re.finditer(pattern, content):
        path = match.group(1)
        methods_str = match.group(2)
        methods = ['GET']
        if methods_str:
            methods = [m.strip().strip("'\"") for m in methods_str.split(',')]

        routes.append({
            "path": path,
            "methods": methods,
            "file": filepath,
            "framework": "Flask"
        })

    return routes


def scan_fastapi_routes(content: str, filepath: str) -> List[Dict]:
    """Scan Python file for FastAPI routes."""
    routes = []
    # Match @app.get, @app.post, @router.get, etc.
    pattern = r'@\w+\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'

    for match in re.finditer(pattern, content, re.IGNORECASE):
        method = match.group(1).upper()
        path = match.group(2)

        routes.append({
            "path": path,
            "methods": [method],
            "file": filepath,
            "framework": "FastAPI"
        })

    return routes


def scan_express_routes(content: str, filepath: str) -> List[Dict]:
    """Scan JavaScript file for Express routes."""
    routes = []
    # Match app.get, router.post, etc.
    pattern = r'(?:app|router)\.(get|post|put|delete|patch)\([\'"`]([^\'"]+)[\'"`]'

    for match in re.finditer(pattern, content, re.IGNORECASE):
        method = match.group(1).upper()
        path = match.group(2)

        routes.append({
            "path": path,
            "methods": [method],
            "file": filepath,
            "framework": "Express"
        })

    return routes


def scan_django_routes(content: str, filepath: str) -> List[Dict]:
    """Scan Python file for Django URL patterns."""
    routes = []
    # Match path('...', ...) and url(r'...', ...)
    pattern = r'(?:path|url)\([\'"]([^\'"]+)[\'"]'

    for match in re.finditer(pattern, content):
        path = match.group(1)

        routes.append({
            "path": path,
            "methods": ["GET"],  # Django doesn't specify method in urls.py
            "file": filepath,
            "framework": "Django"
        })

    return routes


def scan_nextjs_routes(filepath: str) -> List[Dict]:
    """Infer Next.js routes from file path structure."""
    routes = []

    # Check if it's in pages or app directory
    path_str = str(filepath)

    if '/pages/' in path_str or '/app/' in path_str:
        # Extract route from file path
        if '/pages/' in path_str:
            route = path_str.split('/pages/')[-1]
        else:
            route = path_str.split('/app/')[-1]

        # Convert to route
        route = '/' + route
        route = re.sub(r'\.(js|jsx|ts|tsx)$', '', route)
        route = re.sub(r'/index$', '', route)
        route = re.sub(r'\[([^\]]+)\]', r':\1', route)  # [id] -> :id

        if route:
            routes.append({
                "path": route or '/',
                "methods": ["GET"],
                "file": filepath,
                "framework": "Next.js"
            })

    return routes


def scan_react_router_routes(content: str, filepath: str) -> List[Dict]:
    """Scan for React Router routes."""
    routes = []
    # Match <Route path="..." /> patterns
    pattern = r'<Route[^>]*path=[\'"]([^\'"]+)[\'"]'

    for match in re.finditer(pattern, content):
        path = match.group(1)

        routes.append({
            "path": path,
            "methods": ["GET"],
            "file": filepath,
            "framework": "React Router"
        })

    return routes


def scan_target_project_routes() -> Dict:
    """Scan the target project directory for all routes."""
    all_routes = []
    files_scanned = 0

    if not TARGET_PROJECT_DIR.exists():
        return {
            "error": f"Target directory not found: {TARGET_PROJECT_DIR}",
            "routes": [],
            "files_scanned": 0
        }

    # Scan all relevant files
    for filepath in TARGET_PROJECT_DIR.rglob("*"):
        if not filepath.is_file():
            continue

        # Skip common non-essential directories
        path_str = str(filepath)
        if any(skip in path_str for skip in ['node_modules', '__pycache__', 'venv', '.git', 'dist', 'build']):
            continue

        if filepath.suffix not in ALLOWED_EXTENSIONS:
            continue

        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
            rel_path = str(filepath.relative_to(TARGET_PROJECT_DIR))
            files_scanned += 1

            # Python files
            if filepath.suffix == '.py':
                all_routes.extend(scan_flask_routes(content, rel_path))
                all_routes.extend(scan_fastapi_routes(content, rel_path))
                all_routes.extend(scan_django_routes(content, rel_path))

            # JavaScript/TypeScript files
            elif filepath.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                all_routes.extend(scan_express_routes(content, rel_path))
                all_routes.extend(scan_react_router_routes(content, rel_path))
                all_routes.extend(scan_nextjs_routes(rel_path))

        except Exception:
            continue

    # Deduplicate routes
    seen = set()
    unique_routes = []
    for route in all_routes:
        key = (route['path'], tuple(route['methods']), route['framework'])
        if key not in seen:
            seen.add(key)
            unique_routes.append(route)

    return {
        "target_project": str(TARGET_PROJECT_DIR),
        "files_scanned": files_scanned,
        "routes_found": len(unique_routes),
        "routes": unique_routes
    }


def get_agent_routes(app) -> List[Dict]:
    """Get routes from the AI Agent Flask app itself."""
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('static'):
            continue

        methods = list(rule.methods - {'HEAD', 'OPTIONS'})
        view_func = app.view_functions.get(rule.endpoint)
        doc = view_func.__doc__.strip() if view_func and view_func.__doc__ else "No description"

        routes.append({
            "path": rule.rule,
            "methods": methods,
            "endpoint": rule.endpoint,
            "description": doc.split('\n')[0]
        })

    routes.sort(key=lambda x: x['path'])
    return routes


def get_all_routes_info(app) -> Dict:
    """Get comprehensive routes information for both agent and target project."""
    agent_routes = get_agent_routes(app)
    target_info = scan_target_project_routes()

    return {
        "generated_at": datetime.now().isoformat(),
        "agent": {
            "backend_url": AGENT_URLS["backend"],
            "frontend_url": AGENT_URLS["frontend"],
            "routes": agent_routes
        },
        "target_project": target_info,
        "summary": {
            "agent_routes": len(agent_routes),
            "target_routes": target_info.get("routes_found", 0),
            "target_files_scanned": target_info.get("files_scanned", 0)
        }
    }


def generate_routes_markdown(app, filepath: Optional[str] = None) -> str:
    """Generate markdown documentation of all routes."""
    info = get_all_routes_info(app)
    target = info['target_project']

    md = f"""# Application Routes Documentation

Generated: {info['generated_at']}

---

## Target Project Routes

**Project Path:** `{target.get('target_project', 'N/A')}`
**Files Scanned:** {target.get('files_scanned', 0)}
**Routes Found:** {target.get('routes_found', 0)}

"""

    if target.get('routes'):
        # Group by framework
        by_framework = {}
        for route in target['routes']:
            fw = route.get('framework', 'Unknown')
            if fw not in by_framework:
                by_framework[fw] = []
            by_framework[fw].append(route)

        for framework, routes in by_framework.items():
            md += f"### {framework} Routes\n\n"
            md += "| Method | Path | File |\n"
            md += "|--------|------|------|\n"
            for route in routes:
                methods = ', '.join(route['methods'])
                md += f"| {methods} | `{route['path']}` | {route['file']} |\n"
            md += "\n"
    else:
        md += "*No routes found in target project.*\n\n"

    md += f"""---

## AI Agent Routes

**Backend URL:** `{info['agent']['backend_url']}`
**Frontend URL:** `{info['agent']['frontend_url']}`

| Method | Path | Description |
|--------|------|-------------|
"""

    for route in info['agent']['routes']:
        methods = ', '.join(route['methods'])
        md += f"| {methods} | `{route['path']}` | {route.get('description', '')} |\n"

    md += """
---

## Quick Reference

### URLs

| Service | URL |
|---------|-----|
"""
    md += f"| AI Agent Backend | {info['agent']['backend_url']} |\n"
    md += f"| AI Agent Frontend | {info['agent']['frontend_url']} |\n"
    md += f"| Target Project | {target.get('target_project', 'N/A')} |\n"

    md += """
---

*Auto-generated by AI Agent. Run `POST /api/routes/export` to regenerate.*
"""

    if filepath:
        Path(filepath).write_text(md)

    return md


def get_routes_for_ai_context(app) -> str:
    """Get routes summary formatted for AI context."""
    info = get_all_routes_info(app)
    target = info['target_project']

    context = f"""
=== APPLICATION URLS ===
AI Agent Backend: {info['agent']['backend_url']}
AI Agent Frontend: {info['agent']['frontend_url']}
Target Project: {target.get('target_project', 'N/A')}

=== TARGET PROJECT ROUTES ===
"""

    if target.get('routes'):
        for route in target['routes']:
            methods = '/'.join(route['methods'])
            context += f"[{methods}] {route['path']} ({route['framework']}) - {route['file']}\n"
    else:
        context += "No routes detected in target project.\n"

    context += "\n=== AI AGENT API ENDPOINTS ===\n"
    for route in info['agent']['routes']:
        methods = '/'.join(route['methods'])
        context += f"[{methods}] {route['path']}\n"

    return context

