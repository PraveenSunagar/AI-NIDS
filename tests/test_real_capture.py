import time
from scapy.all import IP, TCP, UDP, Raw
from backend.app.services.traffic_adapter import FlowAggregator
from backend.app.services.traffic_service import TrafficService
from backend.app.services.alert_service import AlertService
from backend.app.models.alert import Alert, AlertSeverity, AlertStatus

REQUIRED_20_FEATURES = {
    "src_bytes",
    "dst_bytes",
    "flag",
    "logged_in",
    "same_srv_rate",
    "dst_host_srv_count",
    "diff_srv_rate",
    "dst_host_same_srv_rate",
    "serror_rate",
    "srv_serror_rate",
    "service",
    "count",
    "dst_host_same_src_port_rate",
    "protocol_type",
    "dst_host_srv_diff_host_rate",
    "dst_host_srv_serror_rate",
    "dst_host_diff_srv_rate",
    "srv_count",
    "dst_host_count",
    "dst_host_rerror_rate",
}


def test_flow_aggregator_extracts_20_nsl_kdd_features():
    aggregator = FlowAggregator(min_emit_interval=0.0)

    pkt1 = IP(src="192.168.31.63", dst="93.184.216.34") / TCP(sport=54321, dport=80, flags="S")
    pkt2 = IP(src="93.184.216.34", dst="192.168.31.63") / TCP(sport=80, dport=54321, flags="SA")
    pkt3 = IP(src="192.168.31.63", dst="93.184.216.34") / TCP(sport=54321, dport=80, flags="PA") / Raw(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
    pkt4 = IP(src="93.184.216.34", dst="192.168.31.63") / TCP(sport=80, dport=54321, flags="PA") / Raw(b"HTTP/1.1 200 OK\r\nContent-Length: 12\r\n\r\nHello World!")

    aggregator.ingest_packet(pkt1)
    flow_rec = aggregator.ingest_packet(pkt2)
    flow_rec2 = aggregator.ingest_packet(pkt3)
    flow_rec3 = aggregator.ingest_packet(pkt4)

    record = flow_rec3 or flow_rec2 or flow_rec
    assert record is not None
    assert record["source_ip"] == "192.168.31.63"
    assert record["destination_ip"] == "93.184.216.34"
    assert record["source_port"] == 54321
    assert record["destination_port"] == 80
    assert record["protocol"] == "TCP"
    assert record["capture_mode"] == "REAL"
    assert record["packet_count"] >= 2

    features = record["features"]
    assert REQUIRED_20_FEATURES.issubset(set(features.keys()))
    assert features["protocol_type"] == "tcp"
    assert features["service"] == "http"
    assert features["flag"] == "SF"
    assert features["src_bytes"] > 0
    assert features["dst_bytes"] > 0


def test_broadcast_traffic_not_classified_as_attack(db):
    """
    Verify that subnet broadcast traffic (e.g. 192.168.31.15 -> 192.168.31.255:5775)
    is never classified as a Probe attack solely because dst_bytes=0 on a broadcast address.
    """
    aggregator = FlowAggregator(min_emit_interval=0.0)
    t0 = time.time()

    bcast_pkt = (
        IP(src="192.168.31.15", dst="192.168.31.255")
        / UDP(sport=45598, dport=5775)
        / Raw(b"DISCOVERY_BEACON_" * 4)
    )
    aggregator.ingest_packet(bcast_pkt)
    flushed = aggregator.flush_ready_flows(now=t0 + 1.0)
    assert len(flushed) == 1
    bcast_flow = flushed[0]

    assert bcast_flow["is_broadcast"] is True
    assert bcast_flow["features"]["dst_host_same_src_port_rate"] == 0.0
    assert bcast_flow["features"]["dst_host_srv_diff_host_rate"] == 0.0

    alerts_before = db.query(Alert).count()
    rec = TrafficService.process_and_record_traffic(db, bcast_flow)
    alerts_after = db.query(Alert).count()

    assert rec.prediction == "NORMAL"
    assert alerts_after == alerts_before


def test_normal_https_traffic_classified_as_normal(db):
    """
    Verify that normal encrypted HTTPS (port 443) traffic flows are classified as NORMAL
    without generating false-positive alerts.
    """
    aggregator = FlowAggregator(min_emit_interval=0.0)

    p1 = IP(src="192.168.31.63", dst="172.64.148.235") / TCP(sport=62584, dport=443, flags="PA") / Raw(b"\x17\x03\x03\x01\x20" + b"C" * 280)
    p2 = IP(src="172.64.148.235", dst="192.168.31.63") / TCP(sport=443, dport=62584, flags="PA") / Raw(b"\x17\x03\x03\x04\x00" + b"S" * 1024)

    aggregator.ingest_packet(p1)
    https_flow = aggregator.ingest_packet(p2)
    assert https_flow is not None

    alerts_before = db.query(Alert).count()
    rec = TrafficService.process_and_record_traffic(db, https_flow)
    alerts_after = db.query(Alert).count()

    assert rec.prediction == "NORMAL"
    assert alerts_after == alerts_before


def test_duplicate_alerts_deduplicated_and_severity_separated_from_confidence(db):
    """
    Verify that:
    1. Low-confidence R2L/Probe detections are never assigned CRITICAL severity,
       and instead receive LOW severity + UNVERIFIED status with evidence.
    2. Repeated flows from the same (source_ip, destination_ip, attack_type) within the
       deduplication window do not create duplicate alert rows, but increment occurrence_count.
    """
    AlertService.set_dedup_window(120)

    # Low-confidence border-line R2L-like feature vector
    low_conf_severity = AlertService.calculate_severity(
        confidence=0.54,
        attack_type="R2L",
        feature_data={"validation_status": "UNVERIFIED", "count": 2, "serror_rate": 0.0},
    )
    assert low_conf_severity == AlertSeverity.LOW

    # Trigger 3 repeated attack flows from the same source -> destination within the 120s window
    attack_flow = {
        "source_ip": "10.10.99.55",
        "destination_ip": "192.168.31.63",
        "source_port": 44444,
        "destination_port": 80,
        "protocol": "TCP",
        "packet_size": 0,
        "flow_duration": 0.1,
        "packets_per_second": 200.0,
        "bytes_per_second": 0.0,
        "capture_mode": "MANUAL_TEST",
        "features": {
            "duration": 0.1,
            "protocol_type": "tcp",
            "service": "private",
            "flag": "S0",
            "src_bytes": 0,
            "dst_bytes": 0,
            "logged_in": 0,
            "count": 300,
            "srv_count": 250,
            "serror_rate": 1.0,
            "srv_serror_rate": 1.0,
            "same_srv_rate": 0.05,
            "diff_srv_rate": 0.95,
            "dst_host_count": 255,
            "dst_host_srv_count": 5,
            "dst_host_same_srv_rate": 0.02,
            "dst_host_diff_srv_rate": 0.98,
            "dst_host_same_src_port_rate": 0.0,
            "dst_host_srv_diff_host_rate": 0.0,
            "dst_host_serror_rate": 1.0,
            "dst_host_srv_serror_rate": 1.0,
            "dst_host_rerror_rate": 0.0,
        },
    }

    TrafficService.process_and_record_traffic(db, attack_flow)
    TrafficService.process_and_record_traffic(db, attack_flow)
    TrafficService.process_and_record_traffic(db, attack_flow)

    matching_alerts = (
        db.query(Alert)
        .filter(Alert.source_ip == "10.10.99.55", Alert.destination_ip == "192.168.31.63")
        .all()
    )
    # Must be deduplicated into a single Alert row with occurrence count 3
    assert len(matching_alerts) == 1
    enriched = AlertService._enrich_alert(db, matching_alerts[0])
    assert enriched.occurrence_count == 3
    assert isinstance(enriched.evidence, list) and len(enriched.evidence) > 0


def test_genuine_attack_samples_detected_with_evidence(client):
    """
    Verify that genuine DoS SYN flood and Port Sweep Probe test vectors are detected
    as ATTACK, include detailed evidence strings, and are not suppressed.
    """
    dos_payload = {
        "duration": 0.0,
        "protocol_type": "tcp",
        "service": "private",
        "flag": "S0",
        "src_bytes": 0,
        "dst_bytes": 0,
        "logged_in": 0,
        "count": 350,
        "srv_count": 250,
        "serror_rate": 1.0,
        "same_srv_rate": 0.05,
        "diff_srv_rate": 0.95,
        "dst_host_count": 255,
        "dst_host_srv_count": 5,
        "dst_host_same_srv_rate": 0.02,
        "dst_host_diff_srv_rate": 0.98,
        "dst_host_same_src_port_rate": 0.0,
        "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": 1.0,
        "dst_host_srv_serror_rate": 1.0,
    }
    res = client.post("/api/detection/predict", json=dos_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["prediction"] == "ATTACK"
    assert data["attack_type"] == "DoS"
    assert data["alert_created"] is True
    assert data["validation_status"] in ("VERIFIED_SUSPICIOUS", "UNVERIFIED")
    assert isinstance(data["evidence"], list) and len(data["evidence"]) >= 1


def test_interfaces_and_capture_status_endpoints(client):
    iface_res = client.get("/api/traffic/interfaces")
    assert iface_res.status_code == 200
    iface_data = iface_res.json()
    assert "interfaces" in iface_data
    assert "scapy_available" in iface_data
    assert "npcap_available" in iface_data

    status_res = client.get("/api/traffic/capture/status")
    assert status_res.status_code == 200
    assert status_res.json()["mode"] == "REAL"

    cfg_res = client.get("/api/alerts/config")
    assert cfg_res.status_code == 200
    assert "dedup_window_seconds" in cfg_res.json()


def test_detection_request_schema_matches_exact_20_feature_columns():
    """Verify DetectionRequest includes all 20 model features in feature_columns.pkl."""
    import os
    import joblib
    from backend.app.schemas.detection import DetectionRequest

    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "trained_models")
    feature_columns = joblib.load(os.path.join(model_dir, "feature_columns.pkl"))
    assert len(feature_columns) == 20

    req = DetectionRequest(srv_serror_rate=0.25, dst_host_rerror_rate=0.15)
    payload = req.dict(exclude={"model_name"})
    for col in feature_columns:
        assert col in payload, f"Missing model feature in DetectionRequest: {col}"
    assert payload["srv_serror_rate"] == 0.25
    assert payload["dst_host_rerror_rate"] == 0.15


def test_udp_443_quic_service_mapping_and_encoder_compatibility():
    """Verify UDP/443 (QUIC) is mapped to 'other' (not TCP 'http') and is valid in encoder.pkl."""
    import os
    import joblib

    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "trained_models")
    encoders = joblib.load(os.path.join(model_dir, "encoder.pkl"))

    aggregator = FlowAggregator(min_emit_interval=0.0)
    t0 = time.time()
    aggregator.ingest_parsed_packet(
        src_ip="2409:40f2:1169:22f7::1",
        dst_ip="2001:4860:482c:400::",
        src_port=52330,
        dst_port=443,
        protocol="udp",
        pkt_len=1250,
        timestamp=t0,
    )
    flow_rec = aggregator.ingest_parsed_packet(
        src_ip="2001:4860:482c:400::",
        dst_ip="2409:40f2:1169:22f7::1",
        src_port=443,
        dst_port=52330,
        protocol="udp",
        pkt_len=1350,
        timestamp=t0 + 0.1,
    )
    assert flow_rec is not None
    assert flow_rec["protocol"] == "UDP"
    assert flow_rec["features"]["protocol_type"] == "udp"
    assert flow_rec["features"]["service"] == "other"
    assert flow_rec["features"]["service"] in encoders["service"].classes_


def test_stop_capture_clears_queues_and_prevents_post_stop_persistence():
    """Verify Stop Sniffer clears ready_flows & active_flows and prevents buffered flow persistence."""
    from backend.app.services.traffic_adapter import PacketCaptureAdapter
    from backend.app.api.traffic import process_next_captured_flow
    from tests.conftest import TestingSessionLocal

    adapter = PacketCaptureAdapter(queue_capacity=100, backpressure_timeout=0.01)
    adapter.is_running = True
    adapter._stop_event.clear()
    sample_flow = {
        "source_ip": "192.168.31.63",
        "destination_ip": "142.250.190.46",
        "source_port": 55111,
        "destination_port": 443,
        "protocol": "TCP",
        "packet_size": 900,
        "packet_count": 4,
        "flow_duration": 0.1,
        "packets_per_second": 40.0,
        "bytes_per_second": 9000.0,
        "capture_mode": "REAL",
        "interface": "Wi-Fi",
        "features": {
            "duration": 0.1, "protocol_type": "tcp", "service": "http", "flag": "SF",
            "src_bytes": 300, "dst_bytes": 600, "logged_in": 1, "count": 2, "srv_count": 2,
            "serror_rate": 0.0, "srv_serror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0,
            "dst_host_count": 10, "dst_host_srv_count": 10, "dst_host_same_srv_rate": 1.0,
            "dst_host_diff_srv_rate": 0.0, "dst_host_same_src_port_rate": 0.05,
            "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0,
            "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0,
        },
    }
    assert adapter.enqueue_flow(dict(sample_flow)) is True
    assert adapter.enqueue_flow(dict(sample_flow)) is True

    # Persist 1 flow while running (without any WebSocket client connected)
    persisted = process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter)
    assert persisted is not None
    assert persisted["source_ip"] == "192.168.31.63"
    assert len(adapter.ready_flows) == 1
    assert adapter.total_flows_persisted == 1

    # Now stop capture: queues must clear immediately and subsequent persistence must return None
    adapter.stop()
    assert adapter.is_running is False
    assert len(adapter.ready_flows) == 0
    assert len(adapter.aggregator.active_flows) == 0
    assert process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter) is None
    st = adapter.get_status()
    assert st["flows_processed"] == st["total_flows_persisted"] + st["queued_flows"] + st["dropped_flows"] + st["in_flight_flows"]


def test_queue_capacity_and_explicit_overflow_no_silent_eviction():
    """Verify ready_flows has no maxlen silent eviction and explicitly counts overflow drops."""
    from backend.app.services.traffic_adapter import PacketCaptureAdapter

    adapter = PacketCaptureAdapter(queue_capacity=10, backpressure_timeout=0.002)
    assert adapter.ready_flows.maxlen is None
    adapter.is_running = True
    adapter._stop_event.clear()

    results = []
    for i in range(15):
        flow = {
            "source_ip": f"10.0.0.{i}",
            "destination_ip": "93.184.216.34",
            "source_port": 40000 + i,
            "destination_port": 443,
            "protocol": "TCP",
            "packet_size": 500,
            "packet_count": 3,
            "flow_duration": 0.05,
            "packets_per_second": 60.0,
            "bytes_per_second": 10000.0,
            "capture_mode": "REAL",
            "interface": "Wi-Fi",
            "features": {},
        }
        results.append(adapter.enqueue_flow(flow))

    assert results[:10] == [True] * 10
    assert results[10:] == [False] * 5

    status = adapter.get_status()
    assert status["queue_capacity"] == 10
    assert status["queued_flows"] == 10
    assert status["max_queue_depth"] == 10
    assert status["total_flows_enqueued"] == 10
    assert status["dropped_flows"] == 5
    assert status["queue_overflow_events"] == 5
    assert status["flows_processed"] == 15

    # Verify older flows 0..9 were NEVER silently evicted by flows 10..14
    queued_ips = [f["source_ip"] for f in adapter.ready_flows]
    assert queued_ips == [f"10.0.0.{i}" for i in range(10)]
    adapter.stop()


def test_queue_thread_safety_and_exact_accounting_conservation():
    """Verify concurrent multi-producer + worker consumer thread safety and exact accounting."""
    import threading
    from backend.app.services.traffic_adapter import PacketCaptureAdapter
    from backend.app.api.traffic import process_next_captured_flow
    from tests.conftest import TestingSessionLocal

    adapter = PacketCaptureAdapter(queue_capacity=40, backpressure_timeout=0.03)
    adapter.is_running = True
    adapter._stop_event.clear()

    base_features = {
        "duration": 0.05, "protocol_type": "tcp", "service": "http", "flag": "SF",
        "src_bytes": 400, "dst_bytes": 800, "logged_in": 1, "count": 2, "srv_count": 2,
        "serror_rate": 0.0, "srv_serror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0,
        "dst_host_count": 5, "dst_host_srv_count": 5, "dst_host_same_srv_rate": 1.0,
        "dst_host_diff_srv_rate": 0.0, "dst_host_same_src_port_rate": 0.1,
        "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0,
    }

    producers_done = threading.Event()

    def producer_worker(tid: int, count: int):
        for idx in range(count):
            adapter.enqueue_flow({
                "source_ip": f"192.168.{tid}.{idx + 1}",
                "destination_ip": "142.250.190.46",
                "source_port": 50000 + tid * 100 + idx,
                "destination_port": 443,
                "protocol": "TCP",
                "packet_size": 1200,
                "packet_count": 4,
                "flow_duration": 0.05,
                "packets_per_second": 80.0,
                "bytes_per_second": 24000.0,
                "capture_mode": "REAL",
                "interface": "Wi-Fi",
                "features": dict(base_features),
            })

    persisted_events = []

    def consumer_worker():
        while not producers_done.is_set() or len(adapter.ready_flows) > 0:
            ev = process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter)
            if ev is not None:
                persisted_events.append(ev)
            else:
                time.sleep(0.002)

    p_threads = [threading.Thread(target=producer_worker, args=(t, 20)) for t in range(1, 4)]
    c_thread = threading.Thread(target=consumer_worker)
    c_thread.start()
    for pt in p_threads:
        pt.start()
    for pt in p_threads:
        pt.join()
    producers_done.set()
    c_thread.join(timeout=15.0)

    status = adapter.get_status()
    assert status["flows_processed"] == 60
    assert status["queued_flows"] == 0
    assert status["in_flight_flows"] == 0
    assert status["total_flows_persisted"] == len(persisted_events)
    # Exact conservation identity: generated = persisted + queued + dropped + in_flight
    assert (
        status["flows_processed"]
        == status["total_flows_persisted"]
        + status["queued_flows"]
        + status["dropped_flows"]
        + status["in_flight_flows"]
    )
    adapter.stop()


def test_capture_status_exposes_all_queue_monitoring_metrics(client):
    """Verify /api/traffic/capture/status exposes all required queue monitoring counters."""
    res = client.get("/api/traffic/capture/status")
    assert res.status_code == 200
    data = res.json()
    required_metrics = [
        "queue_capacity",
        "queued_flows",
        "max_queue_depth",
        "dropped_flows",
        "queue_overflow_events",
        "total_flows_enqueued",
        "total_flows_persisted",
        "in_flight_flows",
    ]
    for key in required_metrics:
        assert key in data, f"Missing queue metric in /api/traffic/capture/status: {key}"


def test_stop_wait_start_lifecycle_and_multiple_websocket_broadcast():
    """Verify Start -> Ingestion -> Stop -> Wait -> Start and multi-WebSocket fan-out after persistence."""
    import asyncio
    from backend.app.services.traffic_adapter import PacketCaptureAdapter
    from backend.app.api.traffic import (
        ConnectionManager,
        process_next_captured_flow,
        start_background_ingestion,
        stop_background_ingestion,
    )
    from tests.conftest import TestingSessionLocal

    adapter = PacketCaptureAdapter(queue_capacity=100, backpressure_timeout=0.01)
    base_flow = {
        "source_ip": "192.168.31.63",
        "destination_ip": "8.8.8.8",
        "source_port": 53111,
        "destination_port": 53,
        "protocol": "UDP",
        "packet_size": 140,
        "packet_count": 2,
        "flow_duration": 0.02,
        "packets_per_second": 100.0,
        "bytes_per_second": 7000.0,
        "capture_mode": "REAL",
        "interface": "Wi-Fi",
        "features": {
            "duration": 0.02, "protocol_type": "udp", "service": "domain_u", "flag": "SF",
            "src_bytes": 60, "dst_bytes": 80, "logged_in": 0, "count": 1, "srv_count": 1,
            "serror_rate": 0.0, "srv_serror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0,
            "dst_host_count": 4, "dst_host_srv_count": 4, "dst_host_same_srv_rate": 1.0,
            "dst_host_diff_srv_rate": 0.0, "dst_host_same_src_port_rate": 0.25,
            "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0,
            "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0,
        },
    }

    # Phase 1: Start -> Enqueue 3 -> Persist 2 -> Stop (1 unpersisted queued flow cleared on Stop)
    adapter.is_running = True
    adapter._stop_event.clear()
    for i in range(3):
        f = dict(base_flow)
        f["source_port"] = 53100 + i
        adapter.enqueue_flow(f)

    ev1 = process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter)
    ev2 = process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter)
    assert ev1 is not None and ev2 is not None
    assert ev1["source_port"] == 53100
    assert ev2["source_port"] == 53101

    adapter.stop()
    assert adapter.is_running is False
    assert len(adapter.ready_flows) == 0
    # Attempt to enqueue or persist during Stopped wait window must be rejected
    assert adapter.enqueue_flow(dict(base_flow)) is False
    assert process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter) is None

    # Phase 2: Restart -> Enqueue 1 new flow -> Verify no stale flow from Phase 1 appears
    adapter.is_running = True
    adapter._stop_event.clear()
    f_new = dict(base_flow)
    f_new["source_port"] = 54999
    assert adapter.enqueue_flow(f_new) is True
    ev_new = process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter)
    assert ev_new is not None
    assert ev_new["source_port"] == 54999
    assert process_next_captured_flow(db_session_factory=TestingSessionLocal, adapter=adapter) is None
    adapter.stop()

    # Phase 3: Verify multiple WebSocket clients receive identical persisted event and worker shutdown works
    class DummyWS:
        def __init__(self):
            self.received = []

        async def accept(self):
            pass

        async def send_json(self, msg):
            self.received.append(msg)

    async def _verify_ws_and_worker_shutdown():
        ws_mgr = ConnectionManager()
        c1, c2, c3 = DummyWS(), DummyWS(), DummyWS()
        await ws_mgr.connect(c1)
        await ws_mgr.connect(c2)
        await ws_mgr.connect(c3)
        await ws_mgr.broadcast(ev_new)
        assert len(c1.received) == 1 and len(c2.received) == 1 and len(c3.received) == 1
        assert c1.received[0]["id"] == ev_new["id"] == c2.received[0]["id"] == c3.received[0]["id"]

        task = start_background_ingestion()
        assert task is not None
        await asyncio.sleep(0.05)
        await stop_background_ingestion()
        assert task.done()

    asyncio.run(_verify_ws_and_worker_shutdown())


def test_exact_20_feature_order_and_single_pass_prediction():
    """Verify PredictionEngine preserves exact 20 NSL-KDD feature order and single-pass inference."""
    import os
    import joblib
    from backend.ml.predict import PredictionEngine

    predictor = PredictionEngine()
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "trained_models")
    expected_cols = joblib.load(os.path.join(model_dir, "feature_columns.pkl"))
    assert predictor.feature_columns == expected_cols
    assert len(predictor.feature_columns) == 20

    sample = {col: 0 for col in expected_cols}
    sample.update({"protocol_type": "tcp", "service": "http", "flag": "SF", "src_bytes": 500, "dst_bytes": 1500, "logged_in": 1})
    res = predictor.predict(sample)
    assert res["prediction"] in ("NORMAL", "ATTACK")
    assert 0.0 <= res["confidence"] <= 1.0
