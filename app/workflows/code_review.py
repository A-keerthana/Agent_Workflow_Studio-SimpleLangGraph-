# app/workflows/code_review.py

from typing import Any, Dict, List


State = Dict[str, Any]


def _ensure_log(state: State) -> List[str]:
    """Internal helper to always have a list-based log in the state."""
    if "log" not in state or not isinstance(state["log"], list):
        state["log"] = []
    return state["log"]


def extract_functions(state: State) -> State:
    """
    Very small, heuristic "parser" that looks for Python-style function definitions
    and records their names.
    """
    code = state.get("code", "") or ""
    lines = code.splitlines()

    functions: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") and stripped.endswith(":"):
            # def name(...):
            name_part = stripped[4:stripped.index("(")].strip()
            functions.append(name_part)

    new_state = dict(state)
    new_state["functions"] = functions

    log = _ensure_log(new_state)
    log.append(f"[extract_functions] Found {len(functions)} function(s): {functions}")

    return new_state


def check_complexity(state: State) -> State:
    """
    Toy complexity check:
    - Counts branching keywords and uses that as a crude "complexity score".
    - Normalises to a 0–1 range for convenience.
    """
    code = state.get("code", "") or ""
    keywords = ("if ", "for ", "while ", "and ", "or ", "elif ", "case ")

    hits = 0
    for kw in keywords:
        hits += code.count(kw)

    # crude normalisation – after ~20 branches we just cap the score
    raw_score = min(hits, 20)
    complexity_score = raw_score / 20.0

    new_state = dict(state)
    new_state["complexity_score"] = complexity_score

    log = _ensure_log(new_state)
    log.append(
        f"[check_complexity] Branch keywords={hits}, complexity_score={complexity_score:.2f}"
    )

    return new_state


def detect_basic_issues(state: State) -> State:
    """
    Static checks that are easy to implement without any external libs:
    - lines longer than 88 chars
    - TODO / FIXME comments
    - bare 'except:'
    - print() calls (for library-style code)
    """
    code = state.get("code", "") or ""
    lines = code.splitlines()

    issues: List[str] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        if len(line) > 88:
            issues.append(f"Line {idx}: line longer than 88 characters")

        upper = stripped.upper()
        if "TODO" in upper or "FIXME" in upper:
            issues.append(f"Line {idx}: TODO/FIXME comment present")

        if stripped.startswith("except:"):
            issues.append(f"Line {idx}: bare 'except:' – catch a specific exception")

        if "print(" in stripped:
            issues.append(f"Line {idx}: debug print() – consider logging instead")

    new_state = dict(state)
    new_state["issues"] = issues
    new_state["issue_count"] = len(issues)

    log = _ensure_log(new_state)
    log.append(f"[detect_basic_issues] Found {len(issues)} issue(s)")

    return new_state


def suggest_improvements(state: State) -> State:
    """
    Generate human-readable suggestions from complexity and issues.
    Also computes a 'quality_score' between 0 and 1 that the workflow
    will use for looping.
    """
    complexity = float(state.get("complexity_score", 0.0) or 0.0)
    issue_count = int(state.get("issue_count", 0) or 0)

    suggestions: List[str] = []

    if complexity > 0.7:
        suggestions.append(
            "Code looks quite complex – consider splitting large functions "
            "into smaller, focused helpers."
        )
    elif complexity > 0.4:
        suggestions.append(
            "There is some branching complexity – try to simplify nested "
            "conditions where possible."
        )
    else:
        suggestions.append("Overall control flow looks reasonably simple.")

    if issue_count > 0:
        suggestions.append(
            f"There are {issue_count} basic style/robustness issues to fix (see 'issues')."
        )
    else:
        suggestions.append("No obvious style issues detected.")

    # crude quality score: start from 1.0, subtract penalty
    penalty_from_complexity = complexity * 0.4
    penalty_from_issues = min(issue_count * 0.03, 0.6)

    quality_score = max(0.0, 1.0 - penalty_from_complexity - penalty_from_issues)

    new_state = dict(state)
    new_state["suggestions"] = suggestions
    new_state["quality_score"] = round(quality_score, 3)

    log = _ensure_log(new_state)
    log.append(
        f"[suggest_improvements] quality_score={quality_score:.3f}, "
        f"issues={issue_count}, complexity={complexity:.2f}"
    )

    return new_state


def quality_gate(state: State, threshold: float = 0.8) -> State:
    """
    Simple gate that compares the current quality_score against a threshold.
    The engine will use the 'passes_quality_gate' flag for branching.
    """
    score = float(state.get("quality_score", 0.0) or 0.0)
    passes = score >= threshold

    new_state = dict(state)
    new_state["passes_quality_gate"] = passes

    log = _ensure_log(new_state)
    log.append(
        f"[quality_gate] score={score:.3f}, threshold={threshold}, passes={passes}"
    )

    return new_state
