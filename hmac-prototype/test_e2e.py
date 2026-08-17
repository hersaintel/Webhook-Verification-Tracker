# test_e2e.py
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_sign_and_verify_happy_path():
    # 1. Sign a message
    r = client.post("/sign", json={"message": "hello e2e"})
    assert r.status_code == 200
    data = r.json()
    assert "hmac" in data
    tag = data["hmac"]
    assert len(tag) == 64          # sha256 hex length

    # 2. Verify the same message + tag → success
    r2 = client.post("/verify", json={"message": "hello e2e", "hmac": tag})
    assert r2.status_code == 200
    assert r2.json()["valid"] is True

def test_verify_fails_with_wrong_message():
    r = client.post("/sign", json={"message": "original"})
    tag = r.json()["hmac"]

    r2 = client.post("/verify", json={"message": "tampered", "hmac": tag})
    assert r2.status_code == 401
    assert "Invalid HMAC" in r2.json()["detail"]

def test_verify_fails_with_wrong_hmac():
    r = client.post("/sign", json={"message": "test"})
    tag = r.json()["hmac"]

    # Flip a character
    bad_tag = tag[:-1] + ("0" if tag[-1] != "0" else "1")

    r2 = client.post("/verify", json={"message": "test", "hmac": bad_tag})
    assert r2.status_code == 401

def test_sign_requires_message():
    r = client.post("/sign", json={})
    assert r.status_code == 422          # validation error

def test_verify_requires_both_fields():
    r = client.post("/verify", json={"message": "only-message"})
    assert r.status_code == 422