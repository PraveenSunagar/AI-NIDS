def test_predict_endpoint_normal(client):
    payload = {
        "duration": 0.5,
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF",
        "src_bytes": 1200,
        "dst_bytes": 4500,
        "logged_in": 1,
        "count": 2,
        "srv_count": 2,
        "serror_rate": 0.0,
        "same_srv_rate": 1.0,
        "diff_srv_rate": 0.0,
        "dst_host_count": 100,
        "dst_host_srv_count": 200,
        "dst_host_same_srv_rate": 1.0,
        "dst_host_diff_srv_rate": 0.0,
        "dst_host_same_src_port_rate": 0.1,
        "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0
    }
    response = client.post("/api/detection/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "confidence" in data
    assert "model_name" in data

def test_predict_endpoint_attack(client):
    payload = {
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
        "same_srv_rate": 0.1,
        "diff_srv_rate": 0.9,
        "dst_host_count": 255,
        "dst_host_srv_count": 5,
        "dst_host_same_srv_rate": 0.02,
        "dst_host_diff_srv_rate": 0.98,
        "dst_host_same_src_port_rate": 0.0,
        "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": 1.0,
        "dst_host_srv_serror_rate": 1.0
    }
    response = client.post("/api/detection/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] == "ATTACK"
    assert data["alert_created"] is True
