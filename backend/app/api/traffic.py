import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Any, Callable
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db, SessionLocal
from backend.app.schemas.traffic import TrafficRecordResponse, CaptureConfigRequest
from backend.app.services.traffic_service import TrafficService
from backend.app.services.alert_service import AlertService
from backend.app.services.traffic_adapter import (
    real_capture_adapter,
    list_network_interfaces,
    check_npcap_installed,
    check_is_admin,
    SCAPY_AVAILABLE,
    INTERFACE_VISIBILITY_NOTICE,
)
from backend.app.utils.logger import logger

router = APIRouter(prefix="/traffic", tags=["Traffic"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        if websocket not in self.active_connections:
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
_user_manually_stopped = False
_ingestion_task: Optional[asyncio.Task] = None
_ingestion_stop_requested = False
_ingest_executor: Optional[ThreadPoolExecutor] = None


def _get_ingest_executor() -> ThreadPoolExecutor:
    """
    Return the dedicated single-worker executor used to offload blocking ML inference
    and synchronous SQLite persistence from the main asyncio event loop while preserving
    strict FIFO flow ordering and preventing cross-thread session sharing.
    """
    global _ingest_executor
    if _ingest_executor is None:
        _ingest_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="ai-nids-ingest-worker",
        )
    return _ingest_executor


def process_next_captured_flow(
    db_session_factory: Callable[[], Session] = SessionLocal,
    adapter: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """
    Atomically pop one aggregated flow from the capture adapter, run ML inference, and
    persist it to SQLite using a thread-local SQLAlchemy Session created and closed
    within this worker call.
    Synchronized via adapter.persist_lock so Stop Sniffer immediately halts persistence
    and prevents any buffered flows from being written after Stop completes.
    """
    active_adapter = adapter if adapter is not None else real_capture_adapter
    with active_adapter.persist_lock:
        if not active_adapter.is_running:
            return None

        packet = active_adapter.capture_next_packet()
        if packet is None:
            return None

        db = db_session_factory()
        try:
            record = TrafficService.process_and_record_traffic(db, packet)
            active_adapter.mark_flow_persisted()
            feat_meta = record.feature_data if isinstance(record.feature_data, dict) else {}
            return {
                "id": record.id,
                "timestamp": record.timestamp.strftime("%H:%M:%S"),
                "source_ip": record.source_ip,
                "destination_ip": record.destination_ip,
                "source_port": record.source_port,
                "destination_port": record.destination_port,
                "protocol": record.protocol,
                "packet_size": record.packet_size,
                "packet_count": feat_meta.get("packet_count", packet.get("packet_count", 1)),
                "flow_duration": record.flow_duration,
                "packets_per_second": record.packets_per_second,
                "bytes_per_second": record.bytes_per_second,
                "interface": feat_meta.get("interface", active_adapter.interface),
                "capture_mode": feat_meta.get("capture_mode", "REAL"),
                "prediction": record.prediction,
                "attack_type": record.attack_type,
                "confidence": record.confidence,
                "model_name": record.model_name,
                "validation_status": feat_meta.get("validation_status", "NORMAL"),
                "evidence": feat_meta.get("evidence", []),
                "severity": (
                    AlertService.calculate_severity(
                        record.confidence, record.attack_type, feat_meta
                    ).value
                ) if record.prediction == "ATTACK" else "NORMAL",
                "feature_data": feat_meta,
                "capture_status": active_adapter.get_status(),
            }
        except Exception as exc:
            active_adapter.mark_flow_failed(str(exc))
            raise
        finally:
            db.close()


async def _background_flow_ingestion_loop():
    """
    Single application-lifecycle-managed background task that continuously consumes
    captured flows from PacketCaptureAdapter, offloads blocking ML inference and SQLite
    persistence to a dedicated worker thread via run_in_executor, and broadcasts each
    persisted event to all connected WebSocket clients in exact FIFO order.
    """
    global _ingestion_stop_requested
    loop = asyncio.get_running_loop()
    while not _ingestion_stop_requested:
        try:
            if not real_capture_adapter.is_running:
                await asyncio.sleep(0.15)
                continue

            processed_count = 0
            executor = _get_ingest_executor()
            for _ in range(25):
                if not real_capture_adapter.is_running or _ingestion_stop_requested:
                    break
                if len(real_capture_adapter.ready_flows) == 0:
                    break
                event_data = await loop.run_in_executor(executor, process_next_captured_flow)
                if event_data is None:
                    break
                processed_count += 1
                if manager.active_connections:
                    await manager.broadcast(event_data)

            if processed_count == 0:
                await asyncio.sleep(0.08)
            else:
                await asyncio.sleep(0.002)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"Background flow ingestion error: {exc}")
            await asyncio.sleep(0.3)


def start_background_ingestion() -> Optional[asyncio.Task]:
    """Ensure the single background flow ingestion task and worker executor are running."""
    global _ingestion_task, _ingestion_stop_requested
    _ingestion_stop_requested = False
    _get_ingest_executor()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return None

    if _ingestion_task is None or _ingestion_task.done():
        _ingestion_task = loop.create_task(_background_flow_ingestion_loop())
    return _ingestion_task


async def stop_background_ingestion():
    """
    Stop the background flow ingestion task and wait for any in-flight worker thread
    execution to complete cleanly during application shutdown.
    """
    global _ingestion_task, _ingestion_stop_requested, _ingest_executor
    _ingestion_stop_requested = True
    if _ingestion_task is not None and not _ingestion_task.done():
        _ingestion_task.cancel()
        try:
            await _ingestion_task
        except asyncio.CancelledError:
            pass
    _ingestion_task = None

    if _ingest_executor is not None:
        executor_to_close = _ingest_executor
        _ingest_executor = None
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, lambda: executor_to_close.shutdown(wait=True, cancel_futures=True)
        )


@router.get("/interfaces")
def get_network_interfaces() -> Dict[str, Any]:
    """List available Windows Wi-Fi / Ethernet / Loopback network interfaces via Scapy & Npcap."""
    interfaces = list_network_interfaces()
    return {
        "interfaces": interfaces,
        "active_interface": real_capture_adapter.interface,
        "scapy_available": SCAPY_AVAILABLE,
        "npcap_available": check_npcap_installed(),
        "is_admin": check_is_admin(),
        "visibility_notice": INTERFACE_VISIBILITY_NOTICE,
    }


@router.get("/capture/status")
def get_capture_status() -> Dict[str, Any]:
    """Get live packet capture status, active interface, packet/flow statistics, and permission info."""
    return real_capture_adapter.get_status()


@router.post("/capture/config")
async def configure_capture(config: CaptureConfigRequest) -> Dict[str, Any]:
    """Select active network interface and start/stop/restart passive packet capture."""
    global _user_manually_stopped
    action = (config.action or "start").lower()

    if action == "stop":
        _user_manually_stopped = True
        real_capture_adapter.stop()
        return real_capture_adapter.get_status()

    _user_manually_stopped = False
    if config.interface:
        real_capture_adapter.select_interface(config.interface)

    if action in ("start", "restart"):
        real_capture_adapter.start(real_capture_adapter.interface)
        start_background_ingestion()

    return real_capture_adapter.get_status()


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
    """
    Real-time WebSocket endpoint that registers/unregisters clients.
    The single background ingestion task broadcasts every persisted flow to all connected clients.
    """
    await manager.connect(websocket)
    start_background_ingestion()

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)
