# Modern Webhook Signature Verification

A focused prototype that demonstrates secure webhook ingestion using HMAC-SHA256 with timestamp-based replay protection.

## Goal

Accept only valid signed requests and reject everything else:

- Missing signature header
- Invalid signature
- Expired or future timestamp (replay protection)
- Wrong secret

## How It Works

### Signature Format

The sender creates a header in this format:

X-Signature: t=1712345678,v1=a1b2c3d4e5f6...



- `t` = Unix timestamp
- `v1` = HMAC-SHA256 of the string `timestamp.body`

### Verification Steps

1. Check that the `X-Signature` header exists
2. Parse the timestamp and signature
3. Reject if the timestamp is outside the allowed window (±5 minutes)
4. Recompute the HMAC over `timestamp.body`
5. Perform a timing-safe comparison
6. Accept or reject accordingly

## Project Structure

hmac-prototype/
├── app.py                 # FastAPI receiver
├── hmac_service.py        # HMAC helpers + modern verification
├── sender.py              # Simulated warehouse sender
├── test_hmac.py
├── test_e2e.py
├── .env.example
├── .gitignore
└── README.md


## Quick Start

### 1. Setup

``` bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx pytest pytest-cov

2. Environment
export HMAC_SECRET="super-secret-key-change-me"

3. Run the receiver
uvicorn app:app --reload --port 8000

4. Send a valid request
python sender.py
Expected result: HTTP 200 – request accepted.


Demonstration of Rejection Cases

Missing header

curl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"event":"test"}'

Invalid signature

curl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: t=1712345678,v1=invalidsignature" \
  -d '{"event":"test"}'
Wrong secret
HMAC_SECRET="wrong-secret" python sender.py

Expired timestamp (replay)

Manually craft a request with an old timestamp. The receiver will reject it with:

Timestamp outside allowed tolerance (possible replay)

Available Endpoints

MethodPathDescriptionGET/healthHealth 
checkPOST/webhookMain signature verification endpointGET/eventsRecent accepted events (for demo)GET/docsAutomatic API documentation
Security Properties

Timing-safe comparison (hmac.compare_digest)
Timestamp-based replay protection (5-minute tolerance)
Shared secret never sent over the wire
Clear structured rejection logging

Running Tests
python -m pytest -v --cov=hmac_service --cov-report=term-missing