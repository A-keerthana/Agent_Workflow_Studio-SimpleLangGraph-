# 🚀 Agent Workflow Studio  
*A lightweight, extensible workflow engine for building and executing AI-driven agentic pipelines.*

Developed by **Anipalli Keerthana** as part of the **AI Engineering Assignment – Tredence**.

---

## 🌟 Overview

Agent Workflow Studio is a minimal yet powerful **graph-based workflow engine** built with FastAPI.  
Each workflow is modeled as a series of **nodes** (Python functions) that operate over a shared **state dictionary**.

This project demonstrates:

- Clean backend & API architecture  
- Workflow engine design  
- Modular & extensible node execution  
- Asynchronous execution with background workers  
- WebSocket-based log streaming  
- A custom-made **dark-themed Swagger UI** for professional presentation  

---


## 📁 Project Structure

```
ai_workflow_engine/
│
├── app/
│   ├── main.py                 # FastAPI app, routes, APIs, async runners, WebSockets, custom docs
│   ├── engine.py               # Workflow graph engine (nodes, edges, execution)
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── code_review.py         # Implementation of Code Review Mini-Agent workflow
│   ├── static/
│   │   ├── swagger_dark.css       # Dark theme styling
│   │   ├── swagger_overrides.css  # To remove /openapi.json, UI refinements
│   │   └── logo.png               # Custom branding logo
│   └── ...
│
├── test_websocket_logs.py   # Script for testing WebSocket log streaming
├── venv/                    # Python virtual environment
├── requirements.txt
└── README.md
```


---

## 🔧 Core Engine Components

### ✅ **1. Node Registry**

Nodes are simple Python functions mapped by symbolic names:

```python
TOOL_REGISTRY = {
    "extract_functions": extract_functions,
    "check_complexity": check_complexity,
    "detect_basic_issues": detect_basic_issues,
    "suggest_improvements": suggest_improvements,
    "quality_gate": quality_gate,
}

✅ 2. Graph Definition

Each workflow (graph) contains:
    - Node definitions
    - “next node” transitions
    - Optional conditional branching
    - Shared state handling
    - Log tracking

Stored in memory:
    GRAPHS = {...}
    RUNS = {...}


✅ 3. Execution Loop

Each run performs:

1. Load initial state
2. Execute node
3. Update state
4. Append logs
5. Move to next node
6. Stop when:
    - Workflow ends
    - Branch condition triggers
    - A “quality gate” stops execution

4. Code Review Mini-Agent (workflows/code_review.py)

Implements Option A from the assignment:

Node 1 — Extract Functions
Parses Python code → identifies function names.

Node 2 — Check Complexity
Counts branch keywords → calculates an approximate cyclomatic score.

Node 3 — Detect Basic Issues
Flags/Heuristic checks:
   - Missing docstrings
   - Debug prints
   - Large functions
   - Redundant patterns

Node 4 — Suggest Improvements
Uses previous issues + complexity score to generate improvement suggestions.

Node 5 — Quality Gate
Calculates quality score → stops workflow if above threshold.

5. FastAPI Layer (main.py)
Endpoints
Method	URL                     	Purpose
POST	/graph/create	            Register a new workflow graph
POST	/graph/run	                Execute workflow synchronously
GET	    /graph/state/{run_id}       Get final state and logs
POST	/graph/run_async	        Run workflow in background
GET	    /graph/async_state/{run_id}	Poll async workflow state
WS	    /ws/logs/{run_id}	        Stream logs after execution
GET	    /studio                 	Custom Dark Swagger UI


🌓 Custom Dark Swagger UI

Accessible at:

👉 http://127.0.0.1:9000/studio

Features:

  -  Full dark theme
  -  Improved layout & typography
  -  Custom logo & branding
  -  Hidden /openapi.json link
  -  Restored Schemas section for clarity

This creates a polished, interview-ready developer experience.
This improves developer experience and presentation during evaluation.

⚡ Async Execution + WebSockets Log Streaming

Async Run Workflow

POST /graph/run_async returns immediately:
    {
      "run_id": "uuid",
      "status": "queued"
    }
A background task processes the workflow.

WebSocket  Streaming

Connect using:
    
    ws://127.0.0.1:9000/ws/logs/<run_id>

Streamed output includes:
   - Each log line
   - Final status

Testing helper included:
    python test_webSocket_logs.py


📌 How to Run the Project
1. Create/Setup virtual environment :
        python -m venv venv
        .\venv\Scripts\activate
        pip install -r requirements.txt

2. Launch the server :
        uvicorn app.main:app --reload --port 9000

3. Open the custom docs :
     👉 http://127.0.0.1:9000/studio


📈 Future Enhancements

    - Full async node-by-node execution
    - Live log streaming while nodes run
    - DAG validation + cycle detection
    - Parallel branches for independent nodes
    - Persistent graph/run storage (SQLite/Postgres)
    - Visual workflow editor (React/Next.js)
    - LLM-powered intelligent nodes (RAG, embeddings)

🙌 Why This project Stands Out ?

This project shows strong capability in:

    - Backend architecture
    - Workflow/agent system design
    - Asynchronous programming
    - WebSockets
    - Clean API engineering
    - Thoughtful UX & documentation
    - Modular, extensible code
    - Real agentic reasoning



✨ Developed by:
Anipalli Keerthana

Aspiring AI & Agentic Systems Engineer
Passionate about building intelligent systems,scalable automation frameworks.
