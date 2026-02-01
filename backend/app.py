#!/usr/bin/env python3
"""
AI Agent Web Application

Entry point for the Flask-based AI Agent with web UI.
Run with: python -m backend.app (from demo directory)
Or: python backend/app.py (from demo directory)
"""

import logging
from flask import Flask
from flask_cors import CORS

from .config import DEMO_DIR, TARGET_PROJECT_DIR, ALLOWED_EXTENSIONS, CLAUDE_API_KEY
from .agent import UIAgent
from .routes import api
from . import database as db

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DEMO_DIR / "agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# APP FACTORY
# =============================================================================

def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(DEMO_DIR / "templates"),
        static_folder=str(DEMO_DIR / "static")
    )

    # Session configuration
    app.secret_key = 'agentic-ai-demo-secret-key-2024'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS

    # Enable CORS with credentials support
    CORS(app, supports_credentials=True)

    # Initialize database
    db.init_database()

    # Seed default users and project
    db.seed_default_users()
    db.seed_default_project()

    # Initialize agent
    agent = UIAgent(CLAUDE_API_KEY)
    app.config['AGENT'] = agent

    # Register routes
    app.register_blueprint(api)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Endpoint not found"}, 404

    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Server error: {error}")
        return {"error": "Internal server error"}, 500

    return app


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the application."""
    logger.info("Starting AI Agent Backend")
    logger.info(f"Target directory: {TARGET_PROJECT_DIR}")
    logger.info(f"Allowed extensions: {ALLOWED_EXTENSIONS}")

    # Create templates directory if it doesn't exist
    templates_dir = DEMO_DIR / "templates"
    templates_dir.mkdir(exist_ok=True)

    # Create static directory if it doesn't exist
    static_dir = DEMO_DIR / "static"
    static_dir.mkdir(exist_ok=True)

    # Create and run app
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True,
        use_reloader=True
    )


if __name__ == '__main__':
    main()
