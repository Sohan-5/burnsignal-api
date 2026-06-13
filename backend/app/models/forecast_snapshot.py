from sqlalchemy import Column, String, Integer, Numeric, Date, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class ForecastSnapshot(Base):
    __tablename__ = 'forecast_snapshots'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    snapshot_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    tier = Column(String(10), nullable=False)  # 1|2|3a|3b
    data_points = Column(Integer, nullable=False)
    baseline_forecast = Column(Numeric(14, 2), nullable=True)
    pressure_multiplier = Column(Numeric(6, 4), nullable=False, default=1.0)
    final_forecast = Column(Numeric(14, 2), nullable=True)
    predicted_breach_date = Column(Date, nullable=True)
    confidence_score = Column(Numeric(4, 3), nullable=False)
    daily_burn_rate = Column(Numeric(12, 2), nullable=True)
    burn_ratio = Column(Numeric(6, 4), nullable=True)
    signal_values = Column(JSONB, nullable=False, default=dict)

    project = relationship('Project', back_populates='forecast_snapshots')
