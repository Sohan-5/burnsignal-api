from sqlalchemy import Column, String, Text, TIMESTAMP, text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class ToolConnection(Base):
    __tablename__ = 'tool_connections'
    __table_args__ = (UniqueConstraint('org_id', 'provider', name='uq_tool_connections_org_provider'),)

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    provider = Column(String(50), nullable=False)  # trello|jira|github|linear
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    config = Column(JSONB, nullable=False, default=dict)
    last_synced_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    organization = relationship('Organization', back_populates='tool_connections')
    imported_tasks = relationship('ImportedTask', back_populates='connection', cascade='all, delete-orphan')
