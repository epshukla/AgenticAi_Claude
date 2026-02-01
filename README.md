# AI Agent Dashboard

A full-stack application featuring an AI agent powered by Claude, with a Flask backend and React frontend.



<img width="1337" height="785" alt="Screenshot from 2026-02-01 23-07-54" src="https://github.com/user-attachments/assets/dc18985e-30e5-456d-9f81-2ee8edceebeb" />


<img width="1385" height="923" alt="Screenshot from 2026-02-01 23-08-16" src="https://github.com/user-attachments/assets/422c43d6-0e39-4c79-ac67-5dfc57af72c3" />



## Documentation

- [Ticket Resolution Flow](TICKET_FLOW_DIAGRAM.md) - Complete flow diagram of ticket creation, AI analysis, and change application
- [AI Context Efficiency](AI_CONTEXT_EFFICIENCY.md) - Techniques used to minimize token usage and optimize Claude API requests

## Prerequisites

- Python 3.12+
- Node.js 18+
- npm

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd AgenticAi_Claude
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```bash
CLAUDE_API_KEY=your_anthropic_api_key_here
```

### 3. Backend Setup

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 4. Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
cd ..
```

## Running the Application

**Two terminals are required** to run both the backend and frontend servers.

### Terminal 1: Start the Backend

```bash
source venv/bin/activate
python run.py
```

The backend will be available at: http://localhost:8080

### Terminal 2: Start the Frontend

```bash
cd frontend
npm start
```

The frontend will be available at: http://localhost:4000

## Quick Start (Alternative)

You can also use the provided start script to run the backend:

```bash
./start.sh
```

This will automatically:
- Create a virtual environment if needed
- Install dependencies
- Start the backend server

You'll still need to start the frontend separately in another terminal.

## Project Structure

```
.
├── backend/          # Flask backend API
├── frontend/         # React frontend application
├── requirements.txt  # Python dependencies
├── run.py           # Backend entry point
├── start.sh         # Quick start script
└── .env             # Environment variables (create this)
```
