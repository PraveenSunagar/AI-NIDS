from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from backend.app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_email = Column(String(150), nullable=True)
    action = Column(String(100), nullable=False)
    endpoint = Column(String(200), nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata_info = Column(JSON, nullable=True)
