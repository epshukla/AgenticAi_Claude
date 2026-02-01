# Ticket Resolution Flow

This document illustrates the complete flow of ticket creation, AI-powered analysis, and change application in the Agentic-AI Self-Healing Service.

## System Components

| Component | Description | Color |
|-----------|-------------|-------|
| Agentic-AI Service | Self-healing service (this project) | Blue |
| Claude Server | Anthropic's Claude API | Purple |
| Target Project | E-commerce project being analyzed | Green |

---

## Flow Diagram

```mermaid
flowchart TD
    subgraph User["👤 User / Frontend"]
        U1[Create Ticket]
        U2[View AI Suggestion]
        U3[Accept / Reject / Probe]
    end

    subgraph AgenticAI["🤖 Agentic-AI Self-Healing Service (localhost:8080)"]
        style AgenticAI fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

        A1["POST /api/tickets<br/>Create ticket in DB"]
        A2["POST /api/tickets/{id}/ai-resolve<br/>Trigger AI analysis"]
        A3["fetch_target_blueprint()<br/>Get API structure"]
        A4["identify_relevant_files()<br/>Get file list from target"]
        A5["read_file()<br/>Read relevant files only"]
        A6["process_task_two_step()<br/>Build context + prompt"]
        A7["Store AI suggestion<br/>+ proposed changes in DB"]
        A8["POST /api/tickets/{id}/ai-action<br/>Handle user decision"]
        A9["apply_proposed_change()<br/>Write changes to target"]
        A10["reject_proposed_change()<br/>Mark as rejected"]
        A11["chat()<br/>Follow-up conversation"]
    end

    subgraph Claude["🧠 Claude Server (Anthropic API)"]
        style Claude fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px

        C1["Step 1: Identify Files<br/>max_tokens=1024<br/>(lightweight call)"]
        C2["Step 2: Analyze Task<br/>max_tokens=4096<br/>(full analysis)"]
        C3["Generate Code Changes<br/>max_tokens=4096"]
        C4["Chat Response<br/>max_tokens=2048"]
    end

    subgraph Target["🛒 Target Project - E-commerce (localhost:5001)"]
        style Target fill:#e8f5e9,stroke:#388e3c,stroke-width:2px

        T1["GET /api/blueprint_json<br/>Return API structure"]
        T2["Project Files<br/>(src/, routes/, etc.)"]
        T3["Modified Files<br/>(after changes applied)"]
    end

    %% Ticket Creation Flow
    U1 -->|"1. Submit ticket"| A1
    A1 -->|"2. Ticket stored"| U2

    %% AI Resolution Flow
    U2 -->|"3. Request AI analysis"| A2
    A2 -->|"4. Fetch blueprint"| A3
    A3 -->|"5. HTTP GET"| T1
    T1 -->|"6. API routes + credentials"| A3

    A3 -->|"7. Get file list"| A4
    A4 -->|"8. List files"| T2
    T2 -->|"9. File names only"| A4

    A4 -->|"10. Ask which files relevant"| C1
    C1 -->|"11. Return file paths JSON"| A4

    A4 -->|"12. Read selected files"| A5
    A5 -->|"13. Read content"| T2
    T2 -->|"14. File contents"| A5

    A5 -->|"15. Build context"| A6
    A6 -->|"16. Send task + blueprint + files"| C2
    C2 -->|"17. Analysis + FILES_TO_MODIFY"| A6

    A6 -->|"18. For each file to modify"| C3
    C3 -->|"19. Proposed code changes"| A7
    A7 -->|"20. Show suggestion"| U2

    %% User Decision Flow
    U2 -->|"21. User decides"| U3
    U3 -->|"action=accept"| A8
    U3 -->|"action=reject"| A8
    U3 -->|"action=probe"| A8

    A8 -->|"Accept"| A9
    A9 -->|"22. Write files"| T3
    T3 -->|"23. Changes applied ✅"| U3

    A8 -->|"Reject"| A10
    A10 -->|"24. Marked rejected ❌"| U3

    A8 -->|"Probe"| A11
    A11 -->|"25. Follow-up question"| C4
    C4 -->|"26. Additional insights"| U3
```

---

## Detailed Step-by-Step Flow

### Phase 1: Ticket Creation

| Step | Component | Route/Method | Description |
|------|-----------|--------------|-------------|
| 1 | Frontend | `POST /api/tickets` | User creates ticket with title, category, description |
| 2 | Agentic-AI | `db.create_ticket()` | Ticket stored in SQLite database |

### Phase 2: AI Analysis (Two-Step Process)

| Step | Component | Route/Method | Description |
|------|-----------|--------------|-------------|
| 3 | Frontend | `POST /api/tickets/{id}/ai-resolve` | Trigger AI resolution |
| 4-6 | Agentic-AI → Target | `GET /api/blueprint_json` | Fetch API structure from target |
| 7-9 | Agentic-AI → Target | `get_all_files_recursive()` | Get list of all source files |
| 10-11 | Agentic-AI → Claude | `identify_relevant_files()` | **Step 1**: Ask Claude which files are relevant (lightweight) |
| 12-14 | Agentic-AI → Target | `read_file()` | Read only the relevant files |
| 15-17 | Agentic-AI → Claude | `process_task_two_step()` | **Step 2**: Send task + blueprint + files for analysis |
| 18-19 | Agentic-AI → Claude | `propose_file_change()` | Generate proposed code changes |
| 20 | Agentic-AI | `db.update_ticket_ai_suggestion()` | Store suggestion and proposed changes |

### Phase 3: User Decision

| Step | Component | Route/Method | Description |
|------|-----------|--------------|-------------|
| 21 | Frontend | `POST /api/tickets/{id}/ai-action` | User submits decision |

#### If Accept:
| Step | Component | Route/Method | Description |
|------|-----------|--------------|-------------|
| 22-23 | Agentic-AI → Target | `apply_proposed_change()` | Write modified files to target project |

#### If Reject:
| Step | Component | Route/Method | Description |
|------|-----------|--------------|-------------|
| 24 | Agentic-AI | `reject_proposed_change()` | Mark changes as rejected in DB |

#### If Probe:
| Step | Component | Route/Method | Description |
|------|-----------|--------------|-------------|
| 25-26 | Agentic-AI → Claude | `chat()` | Send follow-up question for more insights |

---

## Token Efficiency Points

```mermaid
flowchart LR
    subgraph Efficient["✅ Efficient Techniques Used"]
        style Efficient fill:#e8f5e9,stroke:#388e3c
        E1["Blueprint endpoint<br/>instead of parsing files"]
        E2["Two-step file selection<br/>lightweight first call"]
        E3["Read only relevant files<br/>not entire codebase"]
        E4["Structured context<br/>formatted API info"]
    end

    subgraph Avoided["❌ What We Avoid"]
        style Avoided fill:#ffebee,stroke:#c62828
        X1["Sending all files"]
        X2["Parsing route files"]
        X3["Including node_modules"]
        X4["Raw JSON dumps"]
    end
```

---

## API Routes Summary

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/tickets` | POST | Create new ticket |
| `/api/tickets` | GET | List all tickets |
| `/api/tickets/{id}` | GET | Get ticket details |
| `/api/tickets/{id}/ai-resolve` | POST | Trigger AI analysis |
| `/api/tickets/{id}/ai-action` | POST | Accept/Reject/Probe |
| `/api/tickets/{id}/chat` | POST | Chat about specific ticket |
| `/api/tickets/{id}/proposed-changes` | GET | View proposed changes |
| `/api/proposed-changes/{id}/accept` | POST | Apply a proposed change |
| `/api/proposed-changes/{id}/reject` | POST | Reject a proposed change |
| `/api/target/blueprint` | GET | Proxy to target's blueprint |
| `/api/target/ai-context` | GET | View formatted AI context |
