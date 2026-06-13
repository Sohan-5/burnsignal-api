from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class OrganizationBase(BaseModel):
    name: str
    slug: str
    plan: str = 'free'

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None

class OrganizationOut(OrganizationBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

class MemberOut(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    hourly_rate: Optional[float] = None
    class Config:
        from_attributes = True

class MemberRoleUpdate(BaseModel):
    role: str  # admin|eng_lead|pm|finance|member
