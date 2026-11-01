from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from backend.app.models.alert import AlertSeverity, AlertStatus

class AlertUpdate(BaseModel):
    status: AlertStatus
    acknowledged_by: Optional[str] = None

class AlertDedupConfig(BaseModel):
    dedup_window_seconds: int

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
    validation_status: Optional[str] = None
    evidence: Optional[List[str]] = None
    occurrence_count: Optional[int] = 1

    class Config:
        from_attributes = True
