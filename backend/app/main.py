import os
import sys
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure root workspace is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.traffic import TrafficRecord
from backend.app.models.alert import Alert, AlertSeverity, AlertStatus
from backend.app.security.password import hash_password
from backend.app.services.traffic_adapter import real_capture_adapter
from backend.app.services.alert_service import AlertService
from backend.ml.predict import is_broadcast_or_multicast_address

from backend.app.api.auth import router as auth_router
from backend.app.api.detection import router as detection_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.traffic import (
    router as traffic_router,
    start_background_ingestion,
    stop_background_ingestion,
)
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.models import router as models_router
from backend.app.api.logs import router as logs_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend origin during dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": str(exc),
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(detection_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(traffic_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(models_router, prefix=settings.API_V1_STR)
app.include_router(logs_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_db_seed():
    db = SessionLocal()
    try:
        # Seed initial admin and analyst users if no users exist
        if db.query(User).count() == 0:
            admin_user = User(
                name="Security Admin",
                email="admin@nids.sec",
                password_hash=hash_password("Admin@123456"),
                role=UserRole.ADMIN,
                is_active=True
            )
            analyst_user = User(
                name="SOC Analyst",
                email="analyst@nids.sec",
                password_hash=hash_password("Analyst@123456"),
                role=UserRole.ANALYST,
                is_active=True
            )
            db.add_all([admin_user, analyst_user])
            db.commit()

        # Remove any legacy simulated DemoTrafficAdapter records that lack 'capture_mode' metadata
        legacy_records = [
            r for r in db.query(TrafficRecord).all()
            if not isinstance(r.feature_data, dict) or r.feature_data.get("capture_mode") not in ("REAL", "MANUAL_TEST")
        ]
        if legacy_records:
            legacy_ids = {r.id for r in legacy_records}
            db.query(Alert).filter(Alert.traffic_record_id.in_(legacy_ids)).delete(synchronize_session=False)
            db.query(TrafficRecord).filter(TrafficRecord.id.in_(legacy_ids)).delete(synchronize_session=False)
            db.commit()

        # Reconcile pre-upgrade broadcast false positives and recalibrate low-confidence alerts
        bcast_attack_records = [
            r for r in db.query(TrafficRecord).filter(TrafficRecord.prediction == "ATTACK").all()
            if is_broadcast_or_multicast_address(r.destination_ip)
            and int((r.feature_data or {}).get("count", 1)) <= 30
        ]
        if bcast_attack_records:
            bcast_ids = {r.id for r in bcast_attack_records}
            for r in bcast_attack_records:
                r.prediction = "NORMAL"
                r.attack_type = "Normal"
                fd = dict(r.feature_data or {})
                fd["validation_status"] = "VERIFIED_BENIGN_BROADCAST"
                fd["is_broadcast"] = True
                fd["evidence"] = [
                    f"Destination {r.destination_ip} is a broadcast/multicast address; one-way UDP payload is normal broadcast traffic."
                ]
                r.feature_data = fd
            db.query(Alert).filter(Alert.traffic_record_id.in_(bcast_ids)).delete(synchronize_session=False)
            db.commit()

        # Recalibrate existing low-confidence (< 0.72) alerts to UNVERIFIED / LOW and deduplicate within window
        existing_alerts = db.query(Alert).order_by(Alert.created_at.asc()).all()
        seen_by_flow = {}
        for al in existing_alerts:
            key = (al.source_ip, al.destination_ip, al.attack_type)
            prev = seen_by_flow.get(key)
            if prev is not None and (al.created_at - prev.created_at).total_seconds() <= AlertService.dedup_window_seconds:
                occ = AlertService._extract_occurrence_count(prev.message) + 1
                base_msg = AlertService._strip_occurrence_prefix(prev.message)
                prev.message = f"[{occ}x Flows] {base_msg}"[:255]
                prev.confidence = max(prev.confidence, al.confidence)
                prev.traffic_record_id = al.traffic_record_id
                db.delete(al)
                continue

            if al.confidence < 0.72:
                al.severity = AlertSeverity.LOW
                if al.status == AlertStatus.OPEN:
                    al.status = AlertStatus.UNVERIFIED
                if al.message.startswith("Security Violation:"):
                    al.message = (
                        f"Unverified Anomaly (Needs Investigation): Possible {al.attack_type} pattern "
                        f"from {al.source_ip} -> {al.destination_ip} (ML Confidence: {al.confidence*100:.1f}%)"
                    )[:255]
                if al.traffic_record_id:
                    tr = db.query(TrafficRecord).filter(TrafficRecord.id == al.traffic_record_id).first()
                    if tr:
                        fd = dict(tr.feature_data or {})
                        fd["validation_status"] = "UNVERIFIED"
                        if not fd.get("evidence"):
                            fd["evidence"] = [
                                f"Borderline ML confidence ({al.confidence*100:.1f}%) requires manual verification before treating as confirmed attack"
                            ]
                        tr.feature_data = fd
            seen_by_flow[key] = al
        db.commit()

        # Start real passive packet capture and single background flow ingestion task
        if "pytest" not in sys.modules:
            real_capture_adapter.start()
            start_background_ingestion()
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_capture():
    await stop_background_ingestion()
    real_capture_adapter.stop()

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "capture_mode": "REAL",
        "docs": "/docs"
    }

@app.get("/api")
@app.get("/api/")
def api_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "capture_mode": "REAL",
        "docs_url": "http://localhost:8000/docs",
        "endpoints": {
            "auth": "/api/auth/login",
            "dashboard_stats": "/api/dashboard/stats",
            "traffic_history": "/api/traffic/history",
            "traffic_interfaces": "/api/traffic/interfaces",
            "capture_status": "/api/traffic/capture/status",
            "capture_config": "/api/traffic/capture/config",
            "ml_models": "/api/models/metrics",
            "alerts": "/api/alerts",
            "detection": "/api/detection/predict"
        }
    }
