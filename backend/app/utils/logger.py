import logging
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog

# Setup Python logging
logger = logging.getLogger("AI-NIDS")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(stream_handler)

def log_audit_event(
    db: Session,
    action: str,
    user_id: int = None,
    user_email: str = None,
    endpoint: str = None,
    ip_address: str = None,
    metadata_info: dict = None
):
    """
    Logs an audit event to standard output and persists it in the database audit_logs table.
    """
    msg = f"AuditAction: {action} | User: {user_email or 'System'} | Endpoint: {endpoint or 'N/A'} | IP: {ip_address or 'N/A'}"
    logger.info(msg)

    try:
        audit_entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            endpoint=endpoint,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            metadata_info=metadata_info
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save audit log entry to DB: {e}")
