"""
Database module for the AI Agent.

SQLite database for tracking:
- Users (roles: admin, tester, developer)
- Projects (title, path)
- Tickets (creator, category, status)
- Changes history (project, files affected, ticket reference)
- AI Context (summaries, findings, recommendations)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import json

from .config import DB_PATH


def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with all required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            role TEXT NOT NULL CHECK(role IN ('admin', 'tester', 'developer')),
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            path TEXT NOT NULL,
            description TEXT,
            frontend_url TEXT,
            backend_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL CHECK(category IN ('bug', 'feature', 'task', 'improvement')),
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'resolved', 'closed')),
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high', 'critical')),
            creator_id INTEGER,
            assignee_id INTEGER,
            project_id INTEGER,
            ai_suggestion TEXT,
            ai_suggestion_status TEXT CHECK(ai_suggestion_status IN ('pending', 'accepted', 'rejected', NULL)),
            ai_files_analyzed TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users(id),
            FOREIGN KEY (assignee_id) REFERENCES users(id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    # Changes history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS changes_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            ticket_id INTEGER,
            files_affected TEXT,
            change_type TEXT CHECK(change_type IN ('create', 'modify', 'delete', 'analyze')),
            change_summary TEXT,
            ai_response TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (ticket_id) REFERENCES tickets(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # AI Context table - stores summaries and findings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            context_type TEXT CHECK(context_type IN ('summary', 'finding', 'recommendation', 'note')),
            title TEXT,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    # Proposed changes table - stores AI proposed code changes for review
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proposed_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            file_path TEXT NOT NULL,
            original_content TEXT,
            proposed_content TEXT NOT NULL,
            change_description TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id)
        )
    """)

    conn.commit()
    conn.close()


# =============================================================================
# USER OPERATIONS
# =============================================================================

def create_user(username: str, role: str, email: Optional[str] = None) -> int:
    """Create a new user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, role, email) VALUES (?, ?, ?)",
        (username, role, email)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_users() -> List[Dict]:
    """Get all users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username for login."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def seed_default_users():
    """Seed default users with simple password."""
    import hashlib
    password_hash = hashlib.sha256("demo123".encode()).hexdigest()

    default_users = [
        ("admin1", "admin", "admin1@example.com"),
        ("dev1", "developer", "dev1@example.com"),
        ("dev2", "developer", "dev2@example.com"),
        ("tester1", "tester", "tester1@example.com"),
    ]

    conn = get_connection()
    cursor = conn.cursor()
    for username, role, email in default_users:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, email)
            )
        except Exception:
            pass
    conn.commit()
    conn.close()


# =============================================================================
# PROPOSED CHANGES OPERATIONS
# =============================================================================

def create_proposed_change(
    file_path: str,
    original_content: str,
    proposed_content: str,
    change_description: str,
    ticket_id: Optional[int] = None
) -> int:
    """Create a proposed change for review."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO proposed_changes
           (ticket_id, file_path, original_content, proposed_content, change_description)
           VALUES (?, ?, ?, ?, ?)""",
        (ticket_id, file_path, original_content, proposed_content, change_description)
    )
    conn.commit()
    change_id = cursor.lastrowid
    conn.close()
    return change_id


def get_proposed_change(change_id: int) -> Optional[Dict]:
    """Get a proposed change by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proposed_changes WHERE id = ?", (change_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_proposed_changes_for_ticket(ticket_id: int) -> List[Dict]:
    """Get all proposed changes for a ticket."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM proposed_changes WHERE ticket_id = ? ORDER BY created_at DESC",
        (ticket_id,)
    )
    changes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return changes


def get_pending_proposed_changes() -> List[Dict]:
    """Get all pending proposed changes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM proposed_changes WHERE status = 'pending' ORDER BY created_at DESC"
    )
    changes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return changes


def update_proposed_change_status(change_id: int, status: str) -> bool:
    """Update proposed change status (accepted/rejected)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE proposed_changes
           SET status = ?, resolved_at = ?
           WHERE id = ?""",
        (status, datetime.now(), change_id)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def seed_default_project():
    """Seed default target project if none exists."""
    from .config import TARGET_PROJECT_DIR

    projects = get_projects()
    if not projects:
        create_project(
            title="Target Project",
            path=str(TARGET_PROJECT_DIR),
            description="The main target project for AI analysis",
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:5001"
        )


# =============================================================================
# PROJECT OPERATIONS
# =============================================================================

def create_project(
    title: str,
    path: str,
    description: Optional[str] = None,
    frontend_url: Optional[str] = None,
    backend_url: Optional[str] = None
) -> int:
    """Create a new project."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (title, path, description, frontend_url, backend_url) VALUES (?, ?, ?, ?, ?)",
        (title, path, description, frontend_url, backend_url)
    )
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    return project_id


def get_projects() -> List[Dict]:
    """Get all projects."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects


def get_project_by_id(project_id: int) -> Optional[Dict]:
    """Get project by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# =============================================================================
# TICKET OPERATIONS
# =============================================================================

def create_ticket(
    title: str,
    category: str,
    description: Optional[str] = None,
    creator_id: Optional[int] = None,
    project_id: Optional[int] = None,
    priority: str = "medium"
) -> int:
    """Create a new ticket."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO tickets (title, description, category, creator_id, project_id, priority)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, description, category, creator_id, project_id, priority)
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id


def get_tickets(project_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict]:
    """Get tickets with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT t.*, p.title as project_title
        FROM tickets t
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE 1=1
    """
    params = []

    if project_id:
        query += " AND t.project_id = ?"
        params.append(project_id)
    if status:
        query += " AND t.status = ?"
        params.append(status)

    query += " ORDER BY t.created_at DESC"
    cursor.execute(query, params)
    tickets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tickets


def update_ticket_status(ticket_id: int, status: str) -> bool:
    """Update ticket status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
        (status, datetime.now(), ticket_id)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_ticket_by_id(ticket_id: int) -> Optional[Dict]:
    """Get a single ticket with creator and assignee info."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            t.*,
            creator.username as creator_username,
            creator.role as creator_role,
            assignee.username as assignee_username,
            assignee.role as assignee_role,
            p.title as project_title
        FROM tickets t
        LEFT JOIN users creator ON t.creator_id = creator.id
        LEFT JOIN users assignee ON t.assignee_id = assignee.id
        LEFT JOIN projects p ON t.project_id = p.id
        WHERE t.id = ?
    """, (ticket_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        ticket = dict(row)
        # Parse JSON fields
        if ticket.get('ai_files_analyzed'):
            ticket['ai_files_analyzed'] = json.loads(ticket['ai_files_analyzed'])
        return ticket
    return None


def update_ticket_ai_suggestion(ticket_id: int, suggestion: str, files_analyzed: List[str]) -> bool:
    """Store AI suggestion for a ticket."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE tickets
           SET ai_suggestion = ?, ai_files_analyzed = ?, ai_suggestion_status = 'pending', updated_at = ?
           WHERE id = ?""",
        (suggestion, json.dumps(files_analyzed), datetime.now(), ticket_id)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def update_ticket_ai_status(ticket_id: int, status: str) -> bool:
    """Update AI suggestion status (accepted/rejected)."""
    conn = get_connection()
    cursor = conn.cursor()

    # If accepted, also resolve the ticket
    if status == 'accepted':
        cursor.execute(
            """UPDATE tickets
               SET ai_suggestion_status = ?, status = 'resolved', updated_at = ?
               WHERE id = ?""",
            (status, datetime.now(), ticket_id)
        )
    else:
        cursor.execute(
            """UPDATE tickets
               SET ai_suggestion_status = ?, updated_at = ?
               WHERE id = ?""",
            (status, datetime.now(), ticket_id)
        )

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


# =============================================================================
# CHANGES HISTORY OPERATIONS
# =============================================================================

def record_change(
    project_id: Optional[int],
    files_affected: List[str],
    change_type: str,
    change_summary: str,
    ai_response: Optional[str] = None,
    ticket_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> int:
    """Record a change in history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO changes_history
           (project_id, ticket_id, files_affected, change_type, change_summary, ai_response, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (project_id, ticket_id, json.dumps(files_affected), change_type, change_summary, ai_response, user_id)
    )
    conn.commit()
    change_id = cursor.lastrowid
    conn.close()
    return change_id


def get_changes_history(project_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """Get changes history with optional project filter."""
    conn = get_connection()
    cursor = conn.cursor()

    if project_id:
        cursor.execute(
            "SELECT * FROM changes_history WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM changes_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )

    changes = []
    for row in cursor.fetchall():
        change = dict(row)
        change['files_affected'] = json.loads(change['files_affected']) if change['files_affected'] else []
        changes.append(change)

    conn.close()
    return changes


# =============================================================================
# AI CONTEXT OPERATIONS
# =============================================================================

def save_ai_context(
    content: str,
    context_type: str = "finding",
    title: Optional[str] = None,
    project_id: Optional[int] = None,
    tags: Optional[List[str]] = None
) -> int:
    """Save AI context/finding."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO ai_context (project_id, context_type, title, content, tags)
           VALUES (?, ?, ?, ?, ?)""",
        (project_id, context_type, title, content, json.dumps(tags) if tags else None)
    )
    conn.commit()
    context_id = cursor.lastrowid
    conn.close()
    return context_id


def get_ai_context(project_id: Optional[int] = None, context_type: Optional[str] = None) -> List[Dict]:
    """Get AI context entries."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM ai_context WHERE 1=1"
    params = []

    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    if context_type:
        query += " AND context_type = ?"
        params.append(context_type)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)

    contexts = []
    for row in cursor.fetchall():
        ctx = dict(row)
        ctx['tags'] = json.loads(ctx['tags']) if ctx['tags'] else []
        contexts.append(ctx)

    conn.close()
    return contexts


def export_ai_context_to_file(filepath: str, project_id: Optional[int] = None) -> str:
    """Export all AI context to a markdown file."""
    contexts = get_ai_context(project_id)

    content = f"""# Agentic AI Context Summary
Generated: {datetime.now().isoformat()}

"""

    # Group by type
    by_type = {}
    for ctx in contexts:
        t = ctx['context_type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(ctx)

    for context_type, items in by_type.items():
        content += f"## {context_type.title()}s\n\n"
        for item in items:
            title = item['title'] or 'Untitled'
            content += f"### {title}\n"
            content += f"*{item['created_at']}*\n\n"
            content += f"{item['content']}\n\n"
            if item['tags']:
                content += f"Tags: {', '.join(item['tags'])}\n\n"
            content += "---\n\n"

    # Write to file
    Path(filepath).write_text(content)
    return filepath
