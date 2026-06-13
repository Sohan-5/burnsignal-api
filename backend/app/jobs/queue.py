"""Lightweight in-memory invalidation queue. Replace with SQS/Redis in production."""
from collections import deque

_queue: deque = deque()

def enqueue(project_id: str):
    if project_id not in _queue:
        _queue.append(project_id)

def drain() -> list:
    items = list(_queue)
    _queue.clear()
    return items
