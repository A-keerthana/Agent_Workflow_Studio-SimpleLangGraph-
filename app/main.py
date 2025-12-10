# app/main.py

from pathlib import Path
from typing import Dict, Any
from uuid import uuid4
import asyncio
import time

from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .engine import (
    GraphCreateRequest,
    GraphCreateResponse,
    RunRequest,
    RunResponse,
    RunStateResponse,
    create_default_code_review_graph,
    create_graph,
    run_graph,
    get_run,
)

# ---------------------------------------------------------------------
# In-memory store for runs that are executed via /graph/run_async
# ---------------------------------------------------------------------
ASYNC_RUNS: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------
# FastAPI app + static files
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent          # .../app
STATIC_DIR = BASE_DIR / "static"                    # .../app/static

app = FastAPI(
    title="AGENT WORKFLOW Studio",
    description=(
        "Internal API for building and running AI workflow graphs. "
        "Developed by @Anipalli Keerthana :)"
    ),
    version="1.0.0",
    docs_url=None,     # disable default Swagger at /docs
    redoc_url=None,    # disable Redoc
)

# serve /static/* from app/static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------
# Custom Dark-Mode Swagger UI at /studio
# ---------------------------------------------------------------------

@app.get("/studio", include_in_schema=False, response_class=HTMLResponse)
async def custom_swagger_docs() -> HTMLResponse:
    """
    Custom Swagger UI with dark theme + custom title/logo.
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Agent Workflow Studio · API Docs</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />

        <!-- Optional custom icon / logo -->
        <link rel="icon" type="image/png" href="/static/logo.png" />

        <!-- Standard Swagger UI CSS from CDN -->
        <link rel="stylesheet"
              type="text/css"
              href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css" />

        <!-- Our dark-mode base styles -->
        <link rel="stylesheet"
              type="text/css"
              href="/static/swagger_dark.css" />

        <!-- Small overrides (hide /openapi.json etc.) -->
        <link rel="stylesheet"
              type="text/css"
              href="/static/swagger_overrides.css" />
    </head>
    <body>
        <div id="swagger-ui"></div>

        <!-- Swagger UI JS from CDN -->
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js"></script>

        <script>
            window.onload = function () {
                window.ui = SwaggerUIBundle({
                    // Still uses /openapi.json internally (standard FastAPI)
                    url: "/openapi.json",
                    dom_id: "#swagger-ui",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",

                    // Make endpoints + Schemas clearly visible
                    docExpansion: "list",          // "list" or "full"
                    defaultModelsExpandDepth: 1
                });
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------
# Startup: create default code review graph
# ---------------------------------------------------------------------

@app.on_event("startup")
def bootstrap_default_graph() -> None:
    """
    When the app starts, create one default Code Review workflow.
    This makes it easy to test without creating a graph first.
    """
    graph_id = create_default_code_review_graph()
    print(f"[startup] Default code_review graph_id = {graph_id}")


# ---------------------------------------------------------------------
# Synchronous graph APIs
# ---------------------------------------------------------------------

@app.post("/graph/create", response_model=GraphCreateResponse, tags=["graphs"])
def create_graph_endpoint(payload: GraphCreateRequest) -> GraphCreateResponse:
    """Create a new workflow graph."""
    graph_id = create_graph(payload)
    return GraphCreateResponse(graph_id=graph_id)


@app.post("/graph/run", response_model=RunResponse, tags=["runs"])
def run_graph_endpoint(payload: RunRequest) -> RunResponse:
    """Run a graph synchronously and return the full result."""
    try:
        result = run_graph(payload.graph_id, payload.initial_state)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return RunResponse(**result)


@app.get("/graph/state/{run_id}", response_model=RunStateResponse, tags=["runs"])
def get_run_state(run_id: str) -> RunStateResponse:
    """Fetch state/log/status for a synchronous run (from engine.get_run)."""
    try:
        run = get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return RunStateResponse(
        run_id=run["id"],
        graph_id=run["graph_id"],
        state=run["state"],
        log=run["log"],
        status=run["status"],
    )


# ---------------------------------------------------------------------
# Asynchronous runs (background job + polling endpoint)
# ---------------------------------------------------------------------

@app.post("/graph/run_async", response_model=RunResponse, tags=["runs"])
def run_graph_async_endpoint(
    payload: RunRequest,
    background_tasks: BackgroundTasks,
) -> RunResponse:
    """
    Run the graph in a background task.

    Returns immediately with status='queued'. The actual work happens
    in the background. Use /graph/async_state/{run_id} to check status
    or /ws/logs/{run_id} to stream logs.
    """
    run_id = str(uuid4())

    # Initial placeholder entry
    ASYNC_RUNS[run_id] = {
        "id": run_id,
        "graph_id": payload.graph_id,
        "state": payload.initial_state,
        "log": ["Run queued for background execution."],
        "status": "queued",
    }

    def _worker() -> None:
        # Simulate a long-running job so the async behaviour is visible
        time.sleep(3)

        try:
            result = run_graph(payload.graph_id, payload.initial_state)
        except Exception as exc:  # noqa: BLE001 - broad on purpose for demo
            ASYNC_RUNS[run_id] = {
                "id": run_id,
                "graph_id": payload.graph_id,
                "state": payload.initial_state,
                "log": [
                    "Run failed while executing in background.",
                    f"Error: {exc}",
                ],
                "status": "failed",
            }
            return

        ASYNC_RUNS[run_id] = {
            "id": run_id,
            "graph_id": result.get("graph_id", payload.graph_id),
            "state": result.get("final_state", payload.initial_state),
            "log": result.get("log", []),
            "status": result.get("status", "completed"),
        }

    background_tasks.add_task(_worker)

    # Immediate response
    return RunResponse(
        run_id=run_id,
        final_state=payload.initial_state,
        log=["Run queued for background execution."],
        status="queued",
    )


@app.get(
    "/graph/async_state/{run_id}",
    response_model=RunStateResponse,
    tags=["runs"],
)
def get_async_run_state(run_id: str) -> RunStateResponse:
    """Check the status of a run created via /graph/run_async."""
    try:
        run = ASYNC_RUNS[run_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return RunStateResponse(
        run_id=run["id"],
        graph_id=run["graph_id"],
        state=run["state"],
        log=run["log"],
        status=run["status"],
    )


# ---------------------------------------------------------------------
# WebSocket for streaming logs
# ---------------------------------------------------------------------

@app.websocket("/ws/logs/{run_id}")
async def websocket_logs(websocket: WebSocket, run_id: str) -> None:
    """
    Stream log lines for a run over WebSocket.

    Works for both:
      - normal /graph/run runs  (stored via engine.get_run)
      - async /graph/run_async runs (stored in ASYNC_RUNS)
    """
    await websocket.accept()

    try:
        # 1) Try async runs
        run = ASYNC_RUNS.get(run_id)

        # 2) If not found, fall back to synchronous runs in engine
        if run is None:
            try:
                run = get_run(run_id)
            except KeyError:
                await websocket.send_json({"error": f"Unknown run_id={run_id}"})
                await websocket.close()
                return

        logs = list(run.get("log", []))
        status = run.get("status", "unknown")

        # Send each log line as a separate message
        for line in logs:
            await websocket.send_json({"run_id": run_id, "message": line})
            await asyncio.sleep(0.2)

        await websocket.send_json({"run_id": run_id, "status": status})
    except WebSocketDisconnect:
        # Client closed the connection – nothing special to do
        pass
    finally:
        await websocket.close()
