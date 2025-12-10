# AGENT WORKFLOW Studio

Internal API for building and running AI workflow graphs.  
Assessment implementation for the AI Engineering role at Tredence.

---

## 1. What this project does

This service exposes a small workflow engine over HTTP.  
Right now it ships with one concrete workflow: a **code-review graph** that analyses a Python function and returns:

- Extracted function names  
- Simple control-flow / complexity score  
- Basic style / robustness issues  
- A lightweight quality score and pass/fail flag  

The idea is that the same engine can be extended later with other graphs (data quality checks, model evaluation pipelines, etc.).

---

## 2. Tech stack

- **Language:** Python 3.11
- **Framework:** FastAPI + Uvicorn
- **Data models:** Pydantic
- **API docs:** Custom Swagger UI at `/studio` (dark theme)
- **Style:** Internal “Agent Workflow Studio” branding

---

## 3. Project layout

```text
ai_workflow_engine/
├── app/
│   ├── main.py                # FastAPI app, custom docs + endpoints
│   ├── engine.py              # In-memory graph + run engine
│   ├── workflows/
│   │   ├── __init__.py        # Register workflows & tools
│   │   └── code_review.py     # Code-review workflow implementation
│   └── static/
│       ├── swagger_dark.css   # Dark theme styles
│       ├── swagger_overrides.css
│       └── logo.png           # Top-left logo in the docs
├── requirements.txt           # Python dependencies
└── README.md
