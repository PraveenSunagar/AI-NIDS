def test_alerts_list_and_update(client):
    # First trigger an attack to generate an alert
    attack_payload = {
        "duration": 0.0,
        "protocol_type": "tcp",
        "service": "private",
        "flag": "S0",
        "src_bytes": 0,
        "dst_bytes": 0,
        "logged_in": 0,
        "count": 400,
        "srv_count": 300,
        "serror_rate": 1.0,
        "same_srv_rate": 0.05,
        "diff_srv_rate": 0.95,
        "dst_host_count": 255,
        "dst_host_srv_count": 2,
        "dst_host_same_srv_rate": 0.01,
        "dst_host_diff_srv_rate": 0.99,
        "dst_host_same_src_port_rate": 0.0,
        "dst_host_srv_diff_host_rate": 0.0,
        "dst_host_serror_rate": 1.0,
        "dst_host_srv_serror_rate": 1.0
    }
    client.post("/api/detection/predict", json=attack_payload)

    # Get alerts
    get_res = client.get("/api/alerts")
    assert get_res.status_code == 200
    alerts = get_res.json()
    assert len(alerts) >= 1

    alert_id = alerts[0]["id"]

    # Register admin user to get auth token
    reg_res = client.post(
        "/api/auth/register",
        json={"name": "Admin Tester", "email": "admin_test@nids.sec", "password": "Password123!", "role": "ADMIN"}
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin_test@nids.sec", "password": "Password123!"}
    )
    token = login_res.json()["access_token"]

    # Acknowledge alert
    update_res = client.put(
        f"/api/alerts/{alert_id}/status",
        json={"status": "ACKNOWLEDGED"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "ACKNOWLEDGED"
