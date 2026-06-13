from sqlalchemy import Column, String, Integer, Numeric, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class HistoricalProject(Base):
    __tablename__ = 'historical_projects'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True)  # NULL = seed data
    source = Column(String(100), nullable=False, default='org')  # org|isbsg|nasa
    duration_type = Column(String(50), nullable=False)  # sprint|medium|program
    project_type = Column(String(100), nullable=True)
    planned_budget = Column(Numeric(14, 2), nullable=True)
    actual_budget = Column(Numeric(14, 2), nullable=True)
    overrun_pct = Column(Numeric(7, 4), nullable=True)
    team_size = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=True)
    phase_cost_breakdown = Column(JSONB, nullable=False, default=dict)
    signal_values_at_overrun = Column(JSONB, nullable=False, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    organization = relationship('Organization', back_populates='historical_projects')
