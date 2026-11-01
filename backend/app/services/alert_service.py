import re
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.alert import Alert, AlertSeverity, AlertStatus
from backend.app.models.traffic import TrafficRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AlertService:
    # Configurable deduplication window in seconds (default: 120s)
    dedup_window_seconds: int = 120

    @classmethod
    def set_dedup_window(cls, seconds: int) -> int:
        cls.dedup_window_seconds = max(0, int(seconds))
        return cls.dedup_window_seconds

    @staticmethod
    def calculate_severity(
        confidence: float,
        attack_type: str,
        feature_data: Optional[Dict[str, Any]] = None,
    ) -> AlertSeverity:
        """
        Separate ML prediction confidence from operational security severity.
        Severity is determined by verified behavioral threat impact + confidence,
        never assigning CRITICAL to low-confidence (50-70%) predictions.
        """
        feat = feature_data or {}
        validation_status = feat.get("validation_status", "VERIFIED_SUSPICIOUS")
        count = int(feat.get("count", 1))
        serror_rate = float(feat.get("serror_rate", 0.0))
        diff_srv_rate = float(feat.get("diff_srv_rate", 0.0))
        dst_host_rerror_rate = float(feat.get("dst_host_rerror_rate", 0.0))

        # Unverified or low-confidence (< 72%) detections are capped at LOW (or MEDIUM if high packet rate)
        if validation_status == "UNVERIFIED" or confidence < 0.72:
            if count >= 100 or serror_rate >= 0.8:
                return AlertSeverity.MEDIUM
            return AlertSeverity.LOW

        # Verified suspicious detections (>= 72% confidence + concrete anomaly indicators)
        has_severe_flood = (count >= 100 and serror_rate >= 0.5) or count >= 250
        has_active_scan = diff_srv_rate >= 0.5 or dst_host_rerror_rate >= 0.5 or serror_rate >= 0.5

        if confidence >= 0.90 and (has_severe_flood or attack_type in ["U2R", "R2L"]):
            return AlertSeverity.CRITICAL
        elif confidence >= 0.82 or has_severe_flood or (confidence >= 0.75 and has_active_scan):
            return AlertSeverity.HIGH
        elif confidence >= 0.72:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW

    @classmethod
    def create_alert_if_attack(cls, db: Session, traffic_record: TrafficRecord) -> Optional[Alert]:
        if traffic_record.prediction != "ATTACK":
            return None

        feat = traffic_record.feature_data if isinstance(traffic_record.feature_data, dict) else {}
        validation_status = feat.get("validation_status", "VERIFIED_SUSPICIOUS")
        severity = cls.calculate_severity(
            traffic_record.confidence,
            traffic_record.attack_type,
            feat,
        )

        # Determine initial alert lifecycle state: UNVERIFIED for uncertain detections, OPEN for verified
        initial_status = (
            AlertStatus.UNVERIFIED
            if (validation_status == "UNVERIFIED" or traffic_record.confidence < 0.72)
            else AlertStatus.OPEN
        )

        now = utc_now()

        # Check configurable flow deduplication window on active (non-RESOLVED) alerts
        if cls.dedup_window_seconds > 0:
            cutoff = now - timedelta(seconds=cls.dedup_window_seconds)
            existing_alert = (
                db.query(Alert)
                .filter(
                    Alert.source_ip == traffic_record.source_ip,
                    Alert.destination_ip == traffic_record.destination_ip,
                    Alert.attack_type == traffic_record.attack_type,
                    Alert.status != AlertStatus.RESOLVED,
                    Alert.created_at >= cutoff,
                )
                .order_by(Alert.created_at.desc())
                .first()
            )
            if existing_alert is not None:
                # Increment occurrence counter in message and update linked record if confidence is higher
                occ = cls._extract_occurrence_count(existing_alert.message) + 1
                existing_alert.confidence = max(existing_alert.confidence, traffic_record.confidence)
                existing_alert.traffic_record_id = traffic_record.id
                base_msg = cls._strip_occurrence_prefix(existing_alert.message)
                existing_alert.message = f"[{occ}x Flows] {base_msg}"[:255]
                db.commit()
                db.refresh(existing_alert)
                return cls._enrich_alert(db, existing_alert)

        if initial_status == AlertStatus.UNVERIFIED:
            msg = (
                f"Unverified Anomaly (Needs Investigation): Possible {traffic_record.attack_type} pattern "
                f"from {traffic_record.source_ip} -> {traffic_record.destination_ip} "
                f"(ML Confidence: {traffic_record.confidence*100:.1f}%)"
            )
        else:
            msg = (
                f"Suspicious Traffic Pattern: {traffic_record.attack_type} anomaly detected "
                f"from {traffic_record.source_ip} -> {traffic_record.destination_ip} "
                f"(ML Confidence: {traffic_record.confidence*100:.1f}%)"
            )

        alert = Alert(
            traffic_record_id=traffic_record.id,
            severity=severity,
            attack_type=traffic_record.attack_type,
            source_ip=traffic_record.source_ip,
            destination_ip=traffic_record.destination_ip,
            message=msg[:255],
            confidence=traffic_record.confidence,
            status=initial_status,
            created_at=now,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return cls._enrich_alert(db, alert)

    @staticmethod
    def _extract_occurrence_count(msg: str) -> int:
        match = re.match(r"^\[(\d+)x Flows\]\s*", msg or "")
        return int(match.group(1)) if match else 1

    @staticmethod
    def _strip_occurrence_prefix(msg: str) -> str:
        return re.sub(r"^\[\d+x Flows\]\s*", "", msg or "")

    @classmethod
    def _enrich_alert(cls, db: Session, alert: Alert) -> Alert:
        occ = cls._extract_occurrence_count(alert.message)
        validation_status = "UNVERIFIED" if alert.status == AlertStatus.UNVERIFIED or alert.confidence < 0.72 else "VERIFIED_SUSPICIOUS"
        evidence: List[str] = []

        if alert.traffic_record_id:
            rec = db.query(TrafficRecord).filter(TrafficRecord.id == alert.traffic_record_id).first()
            if rec and isinstance(rec.feature_data, dict):
                validation_status = rec.feature_data.get("validation_status", validation_status)
                ev = rec.feature_data.get("evidence")
                if isinstance(ev, list):
                    evidence = [str(item) for item in ev]

        if not evidence:
            evidence = [
                f"Flagged as {alert.attack_type} with {alert.confidence*100:.1f}% ML confidence "
                f"(Validation: {validation_status})."
            ]

        setattr(alert, "validation_status", validation_status)
        setattr(alert, "evidence", evidence)
        setattr(alert, "occurrence_count", occ)
        return alert

    @classmethod
    def get_alerts(
        cls,
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Alert]:
        query = db.query(Alert)
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        return [cls._enrich_alert(db, a) for a in alerts]

    @classmethod
    def update_alert_status(
        cls, db: Session, alert_id: int, new_status: AlertStatus, username: str
    ) -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.status = new_status
        if new_status in [AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED]:
            alert.acknowledged_at = utc_now()
            alert.acknowledged_by = username
        db.commit()
        db.refresh(alert)
        return cls._enrich_alert(db, alert)
