import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from backend.app.database import Base

class AlertSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    traffic_record_id = Column(Integer, ForeignKey("traffic_records.id", ondelete="SET NULL"), nullable=True)
    severity = Column(Enum(AlertSeverity), nullable=False)
    attack_type = Column(String(50), nullable=False)
    source_ip = Column(String(50), nullable=False)
    destination_ip = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
