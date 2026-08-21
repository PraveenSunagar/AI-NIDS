def test_register_and_login(client):
    reg_response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": "test@nids.sec",
            "password": "Password123!",
            "role": "ANALYST"
        }
    )
    assert reg_response.status_code == 201
    data = reg_response.json()
    assert data["email"] == "test@nids.sec"

    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "test@nids.sec",
            "password": "Password123!"
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Test /me
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "test@nids.sec"
