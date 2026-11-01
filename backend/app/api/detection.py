from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.detection import DetectionRequest, DetectionResponse
from backend.app.services.traffic_service import TrafficService
from backend.app.services.alert_service import AlertService
from backend.app.models.alert import Alert
from backend.app.utils.logger import log_audit_event

router = APIRouter(prefix="/detection", tags=["Detection"])

@router.post("/predict", response_model=DetectionResponse)
def predict_traffic(request_data: DetectionRequest, request: Request, db: Session = Depends(get_db)):
    feature_dict = request_data.dict(exclude={"model_name"})
    model_choice = request_data.model_name or "best"

    traffic_payload = {
        "source_ip": request.client.host if request.client else "192.168.1.100",
        "destination_ip": "10.0.0.1",
        "source_port": 54321,
        "destination_port": 80 if request_data.service == "http" else 443,
        "protocol": request_data.protocol_type.upper(),
        "packet_size": request_data.src_bytes + request_data.dst_bytes,
        "flow_duration": request_data.duration,
        "packets_per_second": round(request_data.count / (request_data.duration if request_data.duration > 0 else 1.0), 2),
        "bytes_per_second": round((request_data.src_bytes + request_data.dst_bytes) / (request_data.duration if request_data.duration > 0 else 1.0), 2),
        "packet_count": request_data.count,
        "capture_mode": "MANUAL_TEST",
        "interface": "Manual Test Bench",
        "features": feature_dict,
        "model_name": model_choice
    }

    record = TrafficService.process_and_record_traffic(db, traffic_payload)
    feat_meta = record.feature_data if isinstance(record.feature_data, dict) else {}

    alert_created = False
    alert_severity = None
    if record.prediction == "ATTACK":
        alert_created = True
        alert = db.query(Alert).filter(Alert.traffic_record_id == record.id).first()
        if alert:
            alert_severity = alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity)
        else:
            alert_severity = AlertService.calculate_severity(
                record.confidence, record.attack_type, feat_meta
            ).value

    log_audit_event(
        db=db,
        action=f"TRAFFIC_PREDICTION_{record.prediction}",
        endpoint=str(request.url),
        ip_address=request.client.host if request.client else "unknown",
        metadata_info={
            "prediction": record.prediction,
            "attack_type": record.attack_type,
            "confidence": record.confidence,
            "model_name": record.model_name,
            "validation_status": feat_meta.get("validation_status", "NORMAL"),
        }
    )

    return DetectionResponse(
        id=record.id,
        prediction=record.prediction,
        attack_type=record.attack_type,
        confidence=record.confidence,
        model_name=record.model_name,
        timestamp=record.timestamp.isoformat(),
        alert_created=alert_created,
        alert_severity=alert_severity,
        validation_status=feat_meta.get("validation_status", "NORMAL"),
        evidence=feat_meta.get("evidence", []),
    )
