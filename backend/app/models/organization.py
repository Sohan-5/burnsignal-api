from sqlalchemy import Column, String, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    plan = Column(String(50), nullable=False, default='free')
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    users = relationship('User', back_populates='organization', cascade='all, delete-orphan')
    departments = relationship('Department', back_populates='organization', cascade='all, delete-orphan')
    projects = relationship('Project', back_populates='organization', cascade='all, delete-orphan')
    tool_connections = relationship('ToolConnection', back_populates='organization', cascade='all, delete-orphan')
    historical_projects = relationship('HistoricalProject', back_populates='organization')
