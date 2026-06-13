from sqlalchemy import Column, String, Numeric, TIMESTAMP, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    clerk_user_id = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='member')  # admin|eng_lead|pm|finance|member
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

    organization = relationship('Organization', back_populates='users')
    time_entries = relationship('TimeEntry', back_populates='user')
