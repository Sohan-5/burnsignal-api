from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

Provider = Literal['trello', 'jira', 'github', 'linear']

class ConnectionOut(BaseModel):
    id: UUID
    org_id: UUID
    provider: Provider
    last_synced_at: Optional[datetime]
    created_at: datetime
    task_count: int = 0
    class Config:
        from_attributes = True

class TrelloBoardOut(BaseModel):
    id: str
    name: str
    url: str

class SyncConfig(BaseModel):
    board_id: str
    hours_per_story_point: float = 2.0
    status_mapping: dict = {}  # list_name -> status override

class SyncResult(BaseModel):
    tasks_created: int
    tasks_updated: int
    tasks_skipped: int
    synced_at: datetime
