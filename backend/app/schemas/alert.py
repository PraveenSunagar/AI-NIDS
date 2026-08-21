from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from backend.app.models.alert import AlertSeverity, AlertStatus

class AlertUpdate(BaseModel):
    status: AlertStatus
    acknowledged_by: Optional[str] = None

class AlertResponse(BaseModel):
    id: int
    traffic_record_id: Optional[int]
    severity: AlertSeverity
    attack_type: str
    source_ip: str
    destination_ip: str
    message: str
    confidence: float
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None

    class Config:
        from_attributes = True
