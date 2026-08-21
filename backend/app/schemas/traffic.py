from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class TrafficRecordResponse(BaseModel):
    id: int
    timestamp: datetime
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    packet_size: int
    flow_duration: float
    packets_per_second: float
    bytes_per_second: float
    prediction: str
    attack_type: str
    confidence: float
    model_name: str
    feature_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
