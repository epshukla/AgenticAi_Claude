"""
Configuration module for the cross-directory AI agent.

This module defines absolute paths and API credentials for the agent
to access and modify files in a completely separate project directory.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# ===========================================================================
# DIRECTORY CONFIGURATION
# ===========================================================================

# Get the absolute path to the backend directory
BACKEND_DIR = Path(__file__).parent.absolute()

# Get the absolute path to the demo directory (parent of backend)
DEMO_DIR = BACKEND_DIR.parent.absolute()

# Target project directory - COMPLETELY SEPARATE from demo
# Can be set via AGENTIC_AI_TARGET_PROJECT_DIR environment variable
# Otherwise uses relative path from parent directory (portable across machines)
if os.environ.get("AGENTIC_AI_TARGET_PROJECT_DIR"):
    TARGET_PROJECT_DIR = Path(os.environ["AGENTIC_AI_TARGET_PROJECT_DIR"]).absolute()
else:
    # Default: Assumes structure: CyberCypher26/ecommerce-website/
    TARGET_PROJECT_DIR = (DEMO_DIR.parent.parent / "ecommerce-website").absolute()

# ===========================================================================
# FILE ACCESS CONFIGURATION
# ===========================================================================

# Whitelist of allowed file extensions for the agent to modify
# This is a safety check to prevent accidental modification of critical files
ALLOWED_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".config", ".html", ".css", ".js", ".jsx", ".ts", ".tsx"}

# Maximum file size the agent will process (100 KB)
# Prevents processing large binary files or memory exhaustion
MAX_FILE_SIZE = 100 * 1024  # bytes

# ===========================================================================
# CLAUDE API CONFIGURATION
# ===========================================================================

# API key is read from environment variable (required for security)
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY environment variable is required")

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# ===========================================================================
# AGENT BEHAVIOR CONFIGURATION
# ===========================================================================

# System prompt for Claude - defines the agent's instructions
SYSTEM_PROMPT = """You are an expert Python code and documentation agent. Your job is to:

1. Read file contents from a separate project directory
2. Analyze and improve the content
3. Return ONLY the improved file content (never return file paths)

Important constraints:
- You NEVER have direct filesystem access
- You NEVER know the original file paths
- You ONLY return the modified content
- The controller script handles all filesystem operations
- Keep improvements professional and well-documented
"""

# ===========================================================================
# DATABASE CONFIGURATION
# ===========================================================================

DB_PATH = DEMO_DIR / "agent_data.db"

# ===========================================================================
# UTILITY FUNCTIONS
# ===========================================================================

def validate_target_path(file_path: Path) -> bool:
    """
    Validate that a target file path is safe to modify.

    Checks:
    - File exists
    - File is within the target project directory (no escape attempts)
    - File extension is whitelisted
    - File is not too large
    """
    # Resolve to absolute path to prevent ../  escape attempts
    abs_path = file_path.absolute()

    # Check if file is within target directory
    try:
        abs_path.relative_to(TARGET_PROJECT_DIR)
    except ValueError:
        # File is outside target directory
        return False

    # Check if file exists
    if not abs_path.exists():
        return False

    # Check file extension
    if abs_path.suffix not in ALLOWED_EXTENSIONS:
        return False

    # Check file size
    if abs_path.stat().st_size > MAX_FILE_SIZE:
        return False

    return True


if __name__ == "__main__":
    # Debug: Print configuration paths
    print(f"Backend Directory: {BACKEND_DIR}")
    print(f"Demo Directory: {DEMO_DIR}")
    print(f"Target Project Directory: {TARGET_PROJECT_DIR}")
    print(f"Target exists: {TARGET_PROJECT_DIR.exists()}")
    print(f"Database Path: {DB_PATH}")
