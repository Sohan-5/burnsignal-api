from sqlalchemy import Column, String, Numeric, Date, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ToolCost(Base):
    __tablename__ = 'tool_costs'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    tool_name = Column(String(255), nullable=False)
    monthly_cost = Column(Numeric(10, 2), nullable=False)
    active_from = Column(Date, nullable=False)
    active_to = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    project = relationship('Project', back_populates='tool_costs')
    department = relationship('Department', back_populates='tool_costs')
