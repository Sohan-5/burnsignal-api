from sqlalchemy import Column, String, Numeric, Date, Boolean, Text, TIMESTAMP, text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ImportedTask(Base):
    __tablename__ = 'imported_tasks'
    __table_args__ = (UniqueConstraint('project_id', 'connection_id', 'external_id', name='uq_imported_tasks_external'),)

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey('tool_connections.id', ondelete='CASCADE'), nullable=False)
    external_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default='todo')  # todo|in_progress|completed
    estimated_hours = Column(Numeric(6, 2), nullable=True)
    actual_hours = Column(Numeric(6, 2), nullable=True)
    due_date = Column(Date, nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_overdue = Column(Boolean, nullable=False, default=False)
    synced_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    project = relationship('Project', back_populates='imported_tasks')
    connection = relationship('ToolConnection', back_populates='imported_tasks')
