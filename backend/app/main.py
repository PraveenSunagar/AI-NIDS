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
from backend.app.security.password import hash_password
from backend.app.services.traffic_service import TrafficService
from backend.app.services.traffic_adapter import DemoTrafficAdapter

from backend.app.api.auth import router as auth_router
from backend.app.api.detection import router as detection_router
from backend.app.api.alerts import router as alerts_router
from backend.app.api.traffic import router as traffic_router
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
def startup_db_seed():
    db = SessionLocal()
    try:
        # Seed initial admin user if no users exist
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

        # Seed initial realistic traffic records if DB traffic records count < 20
        if TrafficService.get_traffic_history(db, limit=1) == []:
            adapter = DemoTrafficAdapter(attack_ratio=0.35)
            for _ in range(25):
                packet = adapter.capture_next_packet()
                TrafficService.process_and_record_traffic(db, packet)
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs"
    }
