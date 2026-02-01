#!/bin/bash
# Quick start script for Claude Chatbot Agent UI

set -e

echo "🚀 Claude Chatbot Agent - Quick Start"
echo "====================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

echo "✓ Virtual environment ready"

# Activate virtual environment
source .venv/bin/activate
echo "✓ Virtual environment activated"

# Install requirements
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# API key is configured in config.py, no need to prompt

echo ""
echo "🎉 All set! Starting the chatbot..."
echo ""
echo "📱 Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 ui_agent.py
