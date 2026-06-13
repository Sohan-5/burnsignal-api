from sqlalchemy import Column, String, Integer, Date, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Project(Base):
    __tablename__ = 'projects'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='active')  # active|completed|archived
    duration_type = Column(String(50), nullable=False)  # sprint|medium|program
    baseline_task_count = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    organization = relationship('Organization', back_populates='projects')
    department = relationship('Department', back_populates='projects')
    phases = relationship('ProjectPhase', back_populates='project', order_by='ProjectPhase.phase_order', cascade='all, delete-orphan')
    budget = relationship('Budget', back_populates='project', uselist=False, cascade='all, delete-orphan')
    time_entries = relationship('TimeEntry', back_populates='project', cascade='all, delete-orphan')
    tool_costs = relationship('ToolCost', back_populates='project', cascade='all, delete-orphan')
    contractor_costs = relationship('ContractorCost', back_populates='project', cascade='all, delete-orphan')
    imported_tasks = relationship('ImportedTask', back_populates='project', cascade='all, delete-orphan')
    forecast_snapshots = relationship('ForecastSnapshot', back_populates='project', cascade='all, delete-orphan')
