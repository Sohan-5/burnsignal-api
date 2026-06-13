from sqlalchemy import Column, String, Numeric, Date, Text, TIMESTAMP, text, ForeignKey, Computed
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class TimeEntry(Base):
    __tablename__ = 'time_entries'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    phase_id = Column(UUID(as_uuid=True), ForeignKey('project_phases.id', ondelete='SET NULL'), nullable=True)
    entry_date = Column(Date, nullable=False)
    hours = Column(Numeric(6, 2), nullable=False)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(12, 2), Computed('hours * hourly_rate'), nullable=False)
    source = Column(String(50), nullable=False, default='manual')  # manual|trello|jira|github|linear
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    project = relationship('Project', back_populates='time_entries')
    user = relationship('User', back_populates='time_entries')
    phase = relationship('ProjectPhase', back_populates='time_entries')
