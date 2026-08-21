from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.alert import AlertResponse, AlertUpdate
from backend.app.services.alert_service import AlertService
from backend.app.models.user import User
from backend.app.security.authentication import get_current_active_user
from backend.app.security.authorization import allow_analyst_or_admin
from backend.app.utils.logger import log_audit_event

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, ACKNOWLEDGED, RESOLVED"),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return AlertService.get_alerts(db, status=status, severity=severity, limit=limit)

@router.put("/{alert_id}/status", response_model=AlertResponse)
def update_alert_status(
    alert_id: int,
    status_update: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_analyst_or_admin)
):
    updated_alert = AlertService.update_alert_status(
        db, alert_id=alert_id, new_status=status_update.status, username=current_user.name
    )

    if not updated_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found."
        )

    log_audit_event(
        db=db,
        action=f"ALERT_STATUS_{status_update.status.value}",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata_info={"alert_id": alert_id, "new_status": status_update.status.value}
    )

    return updated_alert
