from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.audit_log import AuditLog

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("")
def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if search:
        query = query.filter(
            (AuditLog.user_email.contains(search)) |
            (AuditLog.action.contains(search)) |
            (AuditLog.endpoint.contains(search))
        )
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_email": log.user_email or "System",
            "action": log.action,
            "endpoint": log.endpoint,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat(),
            "metadata": log.metadata_info
        }
        for log in logs
    ]
