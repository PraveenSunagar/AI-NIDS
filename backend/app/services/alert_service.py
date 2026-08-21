from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.alert import Alert, AlertSeverity, AlertStatus
from backend.app.models.traffic import TrafficRecord

class AlertService:
    @staticmethod
    def calculate_severity(confidence: float, attack_type: str) -> AlertSeverity:
        if confidence >= 0.92 or attack_type in ["U2R", "R2L"]:
            return AlertSeverity.CRITICAL
        elif confidence >= 0.85:
            return AlertSeverity.HIGH
        elif confidence >= 0.70:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW

    @classmethod
    def create_alert_if_attack(cls, db: Session, traffic_record: TrafficRecord) -> Optional[Alert]:
        if traffic_record.prediction != "ATTACK":
            return None

        severity = cls.calculate_severity(traffic_record.confidence, traffic_record.attack_type)
        msg = f"Security Violation: {traffic_record.attack_type} intrusion detected from {traffic_record.source_ip} (Confidence: {traffic_record.confidence*100:.1f}%)"

        alert = Alert(
            traffic_record_id=traffic_record.id,
            severity=severity,
            attack_type=traffic_record.attack_type,
            source_ip=traffic_record.source_ip,
            destination_ip=traffic_record.destination_ip,
            message=msg,
            confidence=traffic_record.confidence,
            status=AlertStatus.OPEN,
            created_at=datetime.utcnow()
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_alerts(db: Session, status: Optional[str] = None, severity: Optional[str] = None, limit: int = 100):
        query = db.query(Alert)
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        return query.order_by(Alert.created_at.desc()).limit(limit).all()

    @staticmethod
    def update_alert_status(db: Session, alert_id: int, new_status: AlertStatus, username: str) -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.status = new_status
        if new_status in [AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED]:
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = username
        db.commit()
        db.refresh(alert)
        return alert
