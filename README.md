Agent Workflow Studio
A minimal yet extensible workflow engine for building, executing, and evaluating AI-driven agentic pipelines.

Developed by Anipalli Keerthana as part of the AI Engineering Assignment (Tredence).

🚀 Overview

Agent Workflow Studio is a lightweight but powerful graph-based workflow engine built using FastAPI.
Each workflow is a set of nodes (Python functions) connected through edges, operating on a shared state dictionary.

This submission includes:

A workflow engine that supports:

Node execution

State propagation

Sequential execution

Conditional branching

Simple looping

A Code Review Mini-Agent workflow (Sample Option A from the assignment)

A fully functional REST API for:

Creating workflows

Running workflows

Inspecting workflow state

Support for Async background execution

WebSocket log streaming (after execution)

A custom, dark-themed Swagger UI (/studio)

Clean, modular, production-minded Python code

🏗️ Architecture
ai_workflow_engine/
│
├── app/
│   ├── main.py              → FastAPI application, APIs, async runs, WebSockets, custom docs
│   ├── engine.py            → Workflow graph engine (nodes, edges, execution)
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── code_review.py   → Implementation of Code Review Mini-Agent workflow
│   ├── static/
│   │   ├── swagger_dark.css → Dark theme styling
│   │   ├── swagger_overrides.css → Hide /openapi.json, refine UI
│   │   └── logo.png
│   └── ...
│
├── test_websocket_logs.py   → Script for testing WebSocket log streaming
├── venv/                    → Python virtual environment
├── requirements.txt
└── README.md

🔧 Core Components
1. Workflow Engine (engine.py)

The engine manages:

✅ Node Registry

A dictionary mapping node IDs to actual Python functions:

TOOL_REGISTRY = {
    "extract_functions": extract_functions,
    "check_complexity": check_complexity,
    "detect_basic_issues": detect_basic_issues,
    "suggest_improvements": suggest_improvements,
    "quality_gate": quality_gate,
}

✅ Graph Definition

Each graph contains:

Node definitions

Tool references

Next-node pointers

Optional conditional branches

Stored in-memory:

GRAPHS = {graph_id: {...}}
RUNS = {run_id: {...}}

✅ Execution Loop

Each run proceeds:

Load initial state

Execute node

Update state

Append log

Move to next node

Stop when:

Workflow ends

Quality threshold reached

Branch logic is triggered

2. Code Review Mini-Agent (workflows/code_review.py)

Implements Option A from the assignment:

Node 1 — Extract Functions

Parses Python code → identifies function names.

Node 2 — Check Complexity

Counts branch keywords → calculates an approximate cyclomatic score.

Node 3 — Detect Basic Issues

Heuristic checks:

missing docstrings

debug prints

large functions

redundant patterns

Node 4 — Suggest Improvements

Uses previous issues + complexity score to generate improvement suggestions.

Node 5 — Quality Gate

Calculates quality score → stops workflow if above threshold.

3. FastAPI Layer (main.py)
Endpoints
Method	URL	Purpose
POST	/graph/create	Register a new workflow graph
POST	/graph/run	Execute workflow synchronously
GET	/graph/state/{run_id}	Get final state and logs
POST	/graph/run_async	Run workflow in background
GET	/graph/async_state/{run_id}	Poll async workflow state
WS	/ws/logs/{run_id}	Stream logs after execution
GET	/studio	Custom Dark Swagger UI
🌓 Custom Dark Swagger UI

The /studio endpoint loads a tailored interface:

Dark theme

Modern typography

Clean layout

Hidden /openapi.json exposure

Restored "Schemas" section

Branding: AGENT WORKFLOW Studio

This improves developer experience and presentation during evaluation.

⚡ Async Execution + WebSockets
Async Runs

/graph/run_async returns immediately:

{
  "run_id": "uuid",
  "status": "queued"
}


Background worker performs actual graph execution.

WebSocket Log Streaming

Connect using:

ws://127.0.0.1:9000/ws/logs/<run_id>


The server streams:

Individual log lines

Final status

A test script is provided: test_websocket_logs.py.

📌 How to Run the Project
1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

2. Start the server
uvicorn app.main:app --reload --port 9000

3. Open the custom docs
http://127.0.0.1:9000/studio

🧪 Testing WebSockets
python test_websocket_logs.py


Set:

RUN_ID = "<your-run-id>"


You'll see streamed log messages.

📈 Future Enhancements (Discuss in Interviews)

These ideas demonstrate engineering depth and roadmap thinking:

Full async node execution pipeline

True streaming logs during graph execution (not after)

DAG validation + cycle detection

Support for parallel nodes

SQLite/Postgres backend for persistence

Frontend dashboard for visualizing graphs

Pluggable node execution (LLM calls, embeddings, agents)

Multi-user authentication & RBAC

🙌 Why This Submission Stands Out

This project shows strong capability in:

Workflow engine design

API engineering

Asynchronous programming

WebSockets

Modular architecture

Documentation

Aesthetic/UX thinking

Clean Python code

Agentic reasoning concepts



✨ Developed by:
Anipalli Keerthana

Aspiring AI/Agentic Systems Engineer
Passionate about building the next generation of intelligent systems.