import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db, SessionLocal
from backend.app.schemas.traffic import TrafficRecordResponse
from backend.app.services.traffic_service import TrafficService
from backend.app.services.traffic_adapter import DemoTrafficAdapter

router = APIRouter(prefix="/traffic", tags=["Traffic"])

# Active WebSocket Connections Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()
demo_adapter = DemoTrafficAdapter(attack_ratio=0.30)

@router.get("/history", response_model=List[TrafficRecordResponse])
def get_traffic_history(
    limit: int = Query(100, ge=1, le=500),
    prediction: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return TrafficService.get_traffic_history(
        db, limit=limit, prediction=prediction, protocol=protocol, search=search
    )

@router.websocket("/ws")
async def websocket_traffic_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Generate next simulated traffic packet
            packet = demo_adapter.capture_next_packet()

            # Create DB session for background record insertion
            db = SessionLocal()
            try:
                record = TrafficService.process_and_record_traffic(db, packet)
                event_data = {
                    "id": record.id,
                    "timestamp": record.timestamp.strftime("%H:%M:%S"),
                    "source_ip": record.source_ip,
                    "destination_ip": record.destination_ip,
                    "source_port": record.source_port,
                    "destination_port": record.destination_port,
                    "protocol": record.protocol,
                    "packet_size": record.packet_size,
                    "prediction": record.prediction,
                    "attack_type": record.attack_type,
                    "confidence": record.confidence,
                    "model_name": record.model_name,
                    "severity": ("CRITICAL" if record.confidence >= 0.9 else ("HIGH" if record.confidence >= 0.8 else "MEDIUM")) if record.prediction == "ATTACK" else "NORMAL"
                }
                await websocket.send_json(event_data)
            finally:
                db.close()

            await asyncio.sleep(2.0)  # Stream event every 2 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
