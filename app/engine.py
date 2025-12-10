# app/engine.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from uuid import uuid4

from pydantic import BaseModel, Field

from .workflows import code_review


# -------- Tool registry --------

ToolFunc = callable


TOOL_REGISTRY: Dict[str, ToolFunc] = {
    "extract_functions": code_review.extract_functions,
    "check_complexity": code_review.check_complexity,
    "detect_basic_issues": code_review.detect_basic_issues,
    "suggest_improvements": code_review.suggest_improvements,
    "quality_gate": code_review.quality_gate,
}


# -------- Graph + node models (Pydantic) --------


class NodeSpec(BaseModel):
    """
    One node in the workflow graph.

    - tool: name of the function in TOOL_REGISTRY
    - next: default next node
    - condition_*: optional branching instructions
    """

    id: str
    tool: str
    next: Optional[str] = None

    condition_field: Optional[str] = None
    condition_op: Optional[str] = None  # ">= ", "<", "==", etc.
    condition_value: Optional[Any] = None
    next_on_true: Optional[str] = None
    next_on_false: Optional[str] = None


class GraphCreateRequest(BaseModel):
    name: str
    start_node: str
    nodes: List[NodeSpec]


class GraphCreateResponse(BaseModel):
    graph_id: str


class RunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    run_id: str
    final_state: Dict[str, Any]
    log: List[str]


class RunStateResponse(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    log: List[str]
    status: str


# Internal in-memory stores
_GRAPHS: Dict[str, Dict[str, Any]] = {}
_RUNS: Dict[str, Dict[str, Any]] = {}


# -------- Engine helpers --------


def _evaluate_condition(state: Dict[str, Any], node: NodeSpec) -> Optional[bool]:
    if not node.condition_field or not node.condition_op:
        return None

    left = state.get(node.condition_field)
    right = node.condition_value
    op = node.condition_op

    if op == ">=":
        return left >= right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == "<":
        return left < right
    if op == "==":
        return left == right
    if op == "!=":
        return left != right

    raise ValueError(f"Unsupported condition_op: {op}")


def create_graph(payload: GraphCreateRequest) -> str:
    """
    Store a graph definition in memory and return its ID.
    """
    graph_id = str(uuid4())

    nodes_by_id: Dict[str, NodeSpec] = {n.id: n for n in payload.nodes}

    _GRAPHS[graph_id] = {
        "id": graph_id,
        "name": payload.name,
        "start_node": payload.start_node,
        "nodes": nodes_by_id,
    }

    return graph_id


def run_graph(graph_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
    graph = _GRAPHS.get(graph_id)
    if graph is None:
        raise KeyError(f"Unknown graph_id: {graph_id}")

    run_id = str(uuid4())
    log: List[str] = [f"Starting run {run_id} on graph '{graph['name']}'"]

    state: Dict[str, Any] = dict(initial_state)
    current_node_id: Optional[str] = graph["start_node"]

    steps = 0
    max_steps = 100  # safety against infinite loops

    while current_node_id is not None and steps < max_steps:
        steps += 1
        node: NodeSpec = graph["nodes"][current_node_id]

        if node.tool not in TOOL_REGISTRY:
            raise RuntimeError(f"Tool '{node.tool}' not registered")

        tool_fn = TOOL_REGISTRY[node.tool]
        log.append(f"Node '{node.id}': calling tool '{node.tool}'")

        # call tool; most of ours return a new state dict
        new_state = tool_fn(state)
        if new_state is not None:
            state = new_state

        cond_result = _evaluate_condition(state, node)
        if cond_result is None:
            # no branching – follow default edge
            next_node_id = node.next
        else:
            log.append(
                f"  condition on '{node.condition_field}' {node.condition_op} "
                f"{node.condition_value} -> {cond_result}"
            )
            next_node_id = node.next_on_true if cond_result else node.next_on_false

        current_node_id = next_node_id

    if steps >= max_steps:
        log.append("Max steps reached – stopping to avoid infinite loop.")

    _RUNS[run_id] = {
        "id": run_id,
        "graph_id": graph_id,
        "state": state,
        "log": log,
        "status": "completed",
    }

    return {
        "run_id": run_id,
        "final_state": state,
        "log": log,
    }


def get_run(run_id: str) -> Dict[str, Any]:
    run = _RUNS.get(run_id)
    if run is None:
        raise KeyError(f"Unknown run_id: {run_id}")
    return run


# -------- Helper to create the default Code Review graph --------


def create_default_code_review_graph() -> str:
    """
    Creates a built-in graph implementing:

    1) extract_functions
    2) check_complexity
    3) detect_basic_issues
    4) suggest_improvements
    5) quality_gate (loop until quality_score >= 0.8)
    """

    nodes = [
        NodeSpec(
            id="extract_functions",
            tool="extract_functions",
            next="check_complexity",
        ),
        NodeSpec(
            id="check_complexity",
            tool="check_complexity",
            next="detect_basic_issues",
        ),
        NodeSpec(
            id="detect_basic_issues",
            tool="detect_basic_issues",
            next="suggest_improvements",
        ),
        NodeSpec(
            id="suggest_improvements",
            tool="suggest_improvements",
            next="quality_gate",
        ),
        NodeSpec(
            id="quality_gate",
            tool="quality_gate",
            condition_field="passes_quality_gate",
            condition_op="==",
            condition_value=True,
            next_on_true=None,  # stop
            next_on_false="suggest_improvements",  # loop back
        ),
    ]

    payload = GraphCreateRequest(
        name="code_review_mini_agent",
        start_node="extract_functions",
        nodes=nodes,
    )

    return create_graph(payload)
