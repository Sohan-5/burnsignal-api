"""Converts any integration source into TimeEntry-compatible dicts."""

def normalize_trello_card(card: dict, project_id: str, connection_id: str, hours_per_point: float = 2.0) -> dict:
    estimate = card.get("story_points") or card.get("time_estimate_hours") or hours_per_point
    return {
        "project_id": project_id, "external_id": card["id"], "title": card["name"],
        "status": _map_trello_status(card.get("list_name", "")),
        "estimated_hours": float(estimate) * (hours_per_point if card.get("story_points") else 1),
        "actual_hours": float(card.get("actual_hours", 0)),
        "due_date": card.get("due"), "source": "trello", "connection_id": connection_id,
    }

def normalize_jira_issue(issue: dict, project_id: str, connection_id: str) -> dict:
    pass  # TODO

def normalize_github_issue(issue: dict, project_id: str, connection_id: str) -> dict:
    pass  # TODO

def normalize_linear_issue(issue: dict, project_id: str, connection_id: str) -> dict:
    pass  # TODO

def _map_trello_status(list_name: str) -> str:
    n = list_name.lower()
    if any(w in n for w in ["done", "complete", "finished"]): return "completed"
    if any(w in n for w in ["doing", "progress", "review", "active"]): return "in_progress"
    return "todo"
