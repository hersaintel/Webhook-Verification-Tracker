# Warehouse Webhook Verification & Self-Service Portal

Prototype demonstrating HMAC signature verification for incoming webhooks, combined with a simple customer self-service interface and admin review workflow.

## Overview

This project implements:

- **HMAC-protected webhook endpoint** – verifies the authenticity and integrity of incoming requests from a warehouse system
- **Customer self-service chatbot** – check order status, inventory availability, and submit return requests
- **Return business rule** – returns under $100 are auto-approved; returns of $100 or more require human review
- **Admin review panel** – simple authenticated interface to approve or reject high-value returns

The core security goal is to accept only valid HMAC-signed requests and reject everything else (missing signature, invalid signature, or wrong secret).

## Features

### Webhook Verification
- Timing-safe HMAC comparison (`hmac.compare_digest`)
- Support for SHA-256 (default)
- Clear rejection logging
- End-to-end demo with a simulated warehouse sender

### Customer Self-Service
- Order status lookup by Order ID
- Inventory / stock check by SKU
- Return request submission with automatic threshold logic

### Admin
- Basic authentication (demo credentials)
- View and process pending returns (> $100)

## Tech Stack

- Python 3.13
- FastAPI
- Pydantic
- Uvicorn
- httpx (sender)
- Standard library `hmac` + `hashlib`

## Project Structure
hmac-prototype/
├── app.py                 # Main FastAPI application
├── hmac_service.py        # HMAC generation & verification
├── sender.py              # Simulated warehouse sender
├── static/
│   ├── index.html         # Customer self-service UI
│   └── admin.html         # Admin review panel
├── test_hmac.py           # Unit tests
├── test_e2e.py            # End-to-end tests
├── .env.example
├── .gitignore
└── README.md


## Quick Start

### 1. Clone and set up

```bash
cd hmac-prototype
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx pytest pytest-cov

2. Environment variables
Bashcp .env.example .env
Edit .env:
envHMAC_SECRET=super-secret-key-change-me
ADMIN_USER=admin
ADMIN_PASS=admin123

3. Run the server
Bashexport HMAC_SECRET=super-secret-key-change-me
uvicorn app:app --reload --port 8000

Customer portal: http://127.0.0.1:8000
Admin panel: http://127.0.0.1:8000/admin

Demo: HMAC Verification (End-to-End)
Valid request (accepted)
Bashexport HMAC_SECRET=super-secret-key-change-me
python sender.py
Expected result: HTTP 200 – request accepted.
Invalid requests (rejected)
Missing signature header
Bashcurl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"event":"test"}'
Wrong signature
Bashcurl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-HMAC-Signature: invalidsignature" \
  -d '{"event":"test"}'
Wrong secret
BashHMAC_SECRET=wrong-secret python sender.py
All invalid cases return HTTP 401 and are logged.
Customer Self-Service Examples

status of ORD-2026-88421
stock of SKU-1001
I want to return ORD-2026-77102 (this one is > $100 → pending review)
I want to return ORD-2026-88421 (this one is < $100 → auto-approved)

Admin Access

URL: http://127.0.0.1:8000/admin
Username: admin
Password: admin123

Running Tests
Bashpython -m pytest -v --cov=hmac_service --cov-report=term-missing
Security Notes

Never commit the real .env file
The HMAC secret must be shared only between the sender and the receiver
Timing-safe comparison is used to mitigate timing attacks
Admin credentials are for demonstration only

Future Improvements

Persistent storage (database) instead of in-memory data
Real Google OAuth for admin login
Replay protection (timestamp + nonce)
Rate limiting
Structured audit logging
