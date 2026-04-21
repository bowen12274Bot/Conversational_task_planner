from fastapi.testclient import TestClient


def test_raw_request_returns_contract_shaped_response(client: TestClient) -> None:
    response = client.post(
        "/api/raw-request",
        json={"user_input": "我想把這週的 API 串接工作排出來"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["structured_task_output"] is None
    assert "reply_text" in body
