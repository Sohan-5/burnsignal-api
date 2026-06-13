from sqlalchemy import Column, String, Numeric, Date, Text, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ContractorCost(Base):
    __tablename__ = 'contractor_costs'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    contractor_name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    daily_rate = Column(Numeric(10, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    reason_added = Column(String(100), nullable=False, default='planned')  # deadline_pressure|skill_gap|scope_expansion|planned
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    project = relationship('Project', back_populates='contractor_costs')
