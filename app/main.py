# app/main.py

from pathlib import Path

from fastapi import FastAPI, HTTPException
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

# ---------- FastAPI app + static files ----------

BASE_DIR = Path(__file__).resolve().parent          # .../app
STATIC_DIR = BASE_DIR / "static"                    # .../app/static

app = FastAPI(
    title="AGENT WORKFLOW Studio",
    description="Internal API for building and running AI workflow graphs. Developed by @Anipalli Keerthana :)",
    version="1.0.0",
    docs_url=None,     # disable default Swagger at /docs
    redoc_url=None,    # disable Redoc
)

# serve /static/* from app/static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------- Custom Dark-Mode Swagger UI at /studio ----------

@app.get("/studio", include_in_schema=False, response_class=HTMLResponse)
async def custom_swagger_docs() -> HTMLResponse:
    """
    Custom Swagger UI with dark theme + custom title/logo.
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Agent Workflow Studio · API Docs</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <!-- Optional custom icon / logo -->
        <link rel="icon" type="image/png" href="/static/logo.png">

        <!-- Standard Swagger UI CSS from CDN -->
        <link rel="stylesheet"
              type="text/css"
              href="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui.css">

        <!-- Our dark-mode base styles -->
        <link rel="stylesheet"
              type="text/css"
              href="/static/swagger_dark.css">

        <!-- Small overrides (hide /openapi.json etc.) -->
        <link rel="stylesheet"
              type="text/css"
              href="/static/swagger_overrides.css">
    </head>
    <body>
        <div id="swagger-ui"></div>

        <!-- Swagger UI JS from CDN -->
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist/swagger-ui-standalone-preset.js"></script>

        <script>
            window.onload = function () {
                window.ui = SwaggerUIBundle({
                    // We still use /openapi.json internally,
                    // but we'll hide the visible link via CSS.
                    url: "/openapi.json",
                    dom_id: "#swagger-ui",
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",

                    // ----- IMPORTANT: bring back endpoints + Schemas -----
                    // show tags as a list, but collapsed or expanded
                    docExpansion: "list",           // "list" or "full"
                    // show the Schemas / Models section again
                    defaultModelsExpandDepth: 1
                });
            };
        </script>

    </body>
    </html>
    """
    return HTMLResponse(content=html)


# ---------- Existing startup + endpoints (unchanged) ----------

@app.on_event("startup")
def bootstrap_default_graph() -> None:
    """
    When the app starts, create one default Code Review workflow.
    This makes it easy to test without creating a graph first.
    """
    graph_id = create_default_code_review_graph()
    print(f"[startup] Default code_review graph_id = {graph_id}")


@app.post("/graph/create", response_model=GraphCreateResponse)
def create_graph_endpoint(payload: GraphCreateRequest) -> GraphCreateResponse:
    graph_id = create_graph(payload)
    return GraphCreateResponse(graph_id=graph_id)


@app.post("/graph/run", response_model=RunResponse)
def run_graph_endpoint(payload: RunRequest) -> RunResponse:
    try:
        result = run_graph(payload.graph_id, payload.initial_state)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return RunResponse(**result)


@app.get("/graph/state/{run_id}", response_model=RunStateResponse)
def get_run_state(run_id: str) -> RunStateResponse:
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
