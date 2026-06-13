from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class OrgScoped(BaseModel):
    org_id: UUID

class TimestampMixin(BaseModel):
    created_at: datetime

    class Config:
        from_attributes = True
