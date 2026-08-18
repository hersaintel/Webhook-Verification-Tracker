from fastapi.testclient import TestClient
from app import app
import json

client = TestClient(app)

def test_missing_signature_header():
    response = client.post("/webhook", json={"event": "test"})
    assert response.status_code == 401
    assert "Missing X-HMAC-Signature" in response.json()["detail"]

def test_invalid_signature():
    response = client.post(
        "/webhook",
        content='{"event":"test"}',
        headers={"X-HMAC-Signature": "invalidsignature"}
    )
    assert response.status_code == 401
    assert "Invalid HMAC signature" in response.json()["detail"]

def test_valid_request_still_works():
    # You can keep your existing happy-path test here
    pass