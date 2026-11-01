from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.traffic import TrafficRecord
from backend.app.models.alert import Alert, AlertStatus
from backend.app.services.ml_service import ml_service
from backend.app.services.alert_service import AlertService
from backend.app.services.traffic_adapter import real_capture_adapter


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class TrafficService:
    @staticmethod
    def process_and_record_traffic(db: Session, traffic_data: dict) -> TrafficRecord:
        features = dict(traffic_data.get("features", traffic_data))
        model_choice = traffic_data.get("model_name", "best")
        src_ip = traffic_data.get("source_ip", "0.0.0.0")
        dst_ip = traffic_data.get("destination_ip", "0.0.0.0")

        if "is_broadcast" in traffic_data:
            features["is_broadcast"] = traffic_data["is_broadcast"]

        prediction_result = ml_service.predict_traffic(
            features,
            model_name=model_choice,
            source_ip=src_ip,
            destination_ip=dst_ip,
        )

        # Store capture metadata, validation_status, and evidence alongside features for traceability
        stored_features = dict(features)
        for meta_key in ("packet_count", "interface", "capture_mode"):
            if meta_key in traffic_data:
                stored_features[meta_key] = traffic_data[meta_key]

        stored_features["validation_status"] = prediction_result.get("validation_status", "NORMAL")
        stored_features["evidence"] = prediction_result.get("evidence", [])
        stored_features["is_broadcast"] = prediction_result.get("is_broadcast", False)

        record = TrafficRecord(
            timestamp=utc_now(),
            source_ip=src_ip,
            destination_ip=dst_ip,
            source_port=traffic_data.get("source_port", 0),
            destination_port=traffic_data.get("destination_port", 0),
            protocol=traffic_data.get("protocol", features.get("protocol_type", "tcp")).upper(),
            packet_size=traffic_data.get("packet_size", 0),
            flow_duration=traffic_data.get("flow_duration", features.get("duration", 0.0)),
            packets_per_second=traffic_data.get("packets_per_second", 0.0),
            bytes_per_second=traffic_data.get("bytes_per_second", 0.0),
            feature_data=stored_features,
            prediction=prediction_result["prediction"],
            attack_type=prediction_result["attack_type"],
            confidence=prediction_result["confidence"],
            model_name=prediction_result["model_name"]
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        # Trigger alert creation ONLY if model prediction is ATTACK
        AlertService.create_alert_if_attack(db, record)

        return record

    @staticmethod
    def get_traffic_history(
        db: Session,
        limit: int = 100,
        prediction: Optional[str] = None,
        protocol: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[TrafficRecord]:
        query = db.query(TrafficRecord)
        if prediction:
            query = query.filter(TrafficRecord.prediction == prediction)
        if protocol:
            query = query.filter(TrafficRecord.protocol == protocol.upper())
        if search:
            query = query.filter(
                (TrafficRecord.source_ip.contains(search)) |
                (TrafficRecord.destination_ip.contains(search)) |
                (TrafficRecord.attack_type.contains(search))
            )
        return query.order_by(TrafficRecord.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        total_traffic = db.query(TrafficRecord).count()
        normal_traffic = db.query(TrafficRecord).filter(TrafficRecord.prediction == "NORMAL").count()
        attacks_detected = db.query(TrafficRecord).filter(TrafficRecord.prediction == "ATTACK").count()
        open_alerts = db.query(Alert).filter(Alert.status.in_([AlertStatus.OPEN, AlertStatus.UNVERIFIED])).count()

        detection_rate = round((attacks_detected / total_traffic * 100), 2) if total_traffic > 0 else 0.0

        # Protocol distribution
        proto_counts = db.query(
            TrafficRecord.protocol, func.count(TrafficRecord.id)
        ).group_by(TrafficRecord.protocol).all()
        protocol_dist = {proto: count for proto, count in proto_counts}

        # Attack type distribution
        attack_counts = db.query(
            TrafficRecord.attack_type, func.count(TrafficRecord.id)
        ).filter(TrafficRecord.prediction == "ATTACK").group_by(TrafficRecord.attack_type).all()
        attack_dist = {atk: count for atk, count in attack_counts}

        # Severity distribution
        sev_counts = db.query(
            Alert.severity, func.count(Alert.id)
        ).group_by(Alert.severity).all()
        severity_dist = {str(sev.value if hasattr(sev, 'value') else sev): count for sev, count in sev_counts}

        # Traffic over time (last 20 records aggregated)
        recent_traffic = db.query(TrafficRecord).order_by(TrafficRecord.timestamp.desc()).limit(20).all()
        time_series = [
            {
                "time": t.timestamp.strftime("%H:%M:%S"),
                "prediction": t.prediction,
                "confidence": t.confidence,
                "attack_type": t.attack_type,
                "protocol": t.protocol
            }
            for t in reversed(recent_traffic)
        ]
        recent_mean_confidence = (
            round(sum(t.confidence for t in recent_traffic) / len(recent_traffic), 4)
            if recent_traffic
            else 0.0
        )

        return {
            "total_traffic": total_traffic,
            "normal_traffic": normal_traffic,
            "attacks_detected": attacks_detected,
            "open_alerts": open_alerts,
            "detection_rate": detection_rate,
            "recent_mean_confidence": recent_mean_confidence,
            "protocol_distribution": protocol_dist,
            "attack_distribution": attack_dist,
            "severity_distribution": severity_dist,
            "time_series": time_series,
            "capture_status": real_capture_adapter.get_status()
        }
