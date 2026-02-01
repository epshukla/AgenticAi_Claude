#!/bin/bash
# Quick start script for AI Agent Dashboard

set -e

echo "🚀 AI Agent Dashboard - Quick Start"
echo "===================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "✓ Virtual environment ready"

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install requirements
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "🎉 All set! Starting the backend..."
echo ""
echo "📱 Backend: http://localhost:8080"
echo "📱 Frontend: http://localhost:4000 (run 'cd frontend && npm start' separately)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m backend.app
