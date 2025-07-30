from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship

from abs_repository_core.models import BaseModel


class Integration(BaseModel):
    """Integration model"""
    __tablename__ = "gov_integrations"

    provider_name = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey('gov_users.id'), nullable=False)
    
    # Relationship
    # user = relationship("Users", backref="integrations")
