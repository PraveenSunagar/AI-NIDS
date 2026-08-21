from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from backend.app.database import Base

class TrafficRecord(Base):
    __tablename__ = "traffic_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source_ip = Column(String(50), nullable=False)
    destination_ip = Column(String(50), nullable=False)
    source_port = Column(Integer, nullable=False)
    destination_port = Column(Integer, nullable=False)
    protocol = Column(String(20), nullable=False)
    packet_size = Column(Integer, nullable=False)
    flow_duration = Column(Float, nullable=False)
    packets_per_second = Column(Float, nullable=False)
    bytes_per_second = Column(Float, nullable=False)
    feature_data = Column(JSON, nullable=True)
    prediction = Column(String(20), nullable=False)  # NORMAL / ATTACK
    attack_type = Column(String(50), default="Normal")
    confidence = Column(Float, nullable=False)
    model_name = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
