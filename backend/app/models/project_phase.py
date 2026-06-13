from sqlalchemy import Column, String, Integer, Numeric, Date, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ProjectPhase(Base):
    __tablename__ = 'project_phases'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    phase_order = Column(Integer, nullable=False, default=1)
    planned_start = Column(Date, nullable=False)
    planned_end = Column(Date, nullable=False)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)
    budget_allocation_pct = Column(Numeric(5, 2), nullable=False)
    status = Column(String(50), nullable=False, default='pending')  # pending|active|completed
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    project = relationship('Project', back_populates='phases')
    time_entries = relationship('TimeEntry', back_populates='phase')
