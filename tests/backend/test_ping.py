from fastapi.testclient import TestClient

def test_ping_returns_backend_connected_message(client: TestClient) -> None:
    response = client.get("/api/ping")

    assert response.status_code == 200
    assert response.json() == {"message": "backend connected"}
