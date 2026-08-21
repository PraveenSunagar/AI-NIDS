from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.traffic import TrafficRecord
from backend.app.models.alert import Alert, AlertStatus, AlertSeverity
from backend.app.services.ml_service import ml_service
from backend.app.services.alert_service import AlertService

class TrafficService:
    @staticmethod
    def process_and_record_traffic(db: Session, traffic_data: dict) -> TrafficRecord:
        features = traffic_data.get("features", traffic_data)
        model_choice = traffic_data.get("model_name", "best")

        prediction_result = ml_service.predict_traffic(features, model_name=model_choice)

        record = TrafficRecord(
            timestamp=datetime.utcnow(),
            source_ip=traffic_data.get("source_ip", "192.168.1.50"),
            destination_ip=traffic_data.get("destination_ip", "10.0.0.1"),
            source_port=traffic_data.get("source_port", 44321),
            destination_port=traffic_data.get("destination_port", 80),
            protocol=traffic_data.get("protocol", features.get("protocol_type", "tcp")).upper(),
            packet_size=traffic_data.get("packet_size", 512),
            flow_duration=traffic_data.get("flow_duration", features.get("duration", 1.0)),
            packets_per_second=traffic_data.get("packets_per_second", 10.0),
            bytes_per_second=traffic_data.get("bytes_per_second", 5000.0),
            feature_data=features,
            prediction=prediction_result["prediction"],
            attack_type=prediction_result["attack_type"],
            confidence=prediction_result["confidence"],
            model_name=prediction_result["model_name"]
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        # Trigger alert creation if prediction is ATTACK
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
        open_alerts = db.query(Alert).filter(Alert.status == AlertStatus.OPEN).count()

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

        # Traffic over time (last 10 records aggregated)
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

        return {
            "total_traffic": total_traffic,
            "normal_traffic": normal_traffic,
            "attacks_detected": attacks_detected,
            "open_alerts": open_alerts,
            "detection_rate": detection_rate,
            "protocol_distribution": protocol_dist,
            "attack_distribution": attack_dist,
            "severity_distribution": severity_dist,
            "time_series": time_series
        }
