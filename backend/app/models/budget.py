from sqlalchemy import Column, String, Numeric, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Budget(Base):
    __tablename__ = 'budgets'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, unique=True)
    total_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    headcount_pct = Column(Numeric(5, 2), nullable=False, default=60.00)
    tools_pct = Column(Numeric(5, 2), nullable=False, default=15.00)
    contractors_pct = Column(Numeric(5, 2), nullable=False, default=20.00)
    contingency_pct = Column(Numeric(5, 2), nullable=False, default=5.00)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    project = relationship('Project', back_populates='budget')
