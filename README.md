# Solstice Events – Async Check-in Kiosk

Event check-in service for **Solstice Events Co.**, built after a forced pivot from a synchronous badge-printer API to an **asynchronous queue + webhook** model.

The project also documents the earlier learning path: HMAC webhook verification → modern signed callbacks with replay protection → Redis-backed async check-in.

**Live demo:** https://solstice-checkin.onrender.com

---

## Client problem (pivot)

Originally the kiosk was expected to:

1. Scan an attendee QR code  
2. Call the badge-printer vendor **synchronously** over REST  
3. Wait for success  
4. Only then show **Checked In**  
5. Block duplicate scans (no second badge)

The vendor then **deprecated the synchronous print API** with no deadline extension. The service had to be rebuilt so that:

- A print request is **published to a message queue**
- The kiosk exposes a **webhook** for the completion callback  
- The UI shows **Pending** until confirmation arrives  
- **Duplicate-scan protection** still holds if callbacks arrive late or out of order  

**New technology introduced:** Redis (queue + attendee state).

---

## Solution overview

```text
QR scan / Check In
    → POST/GET /checkin/{id}
    → if already checked_in → 409 (no second print)
    → else status = pending, job pushed to Redis queue

In-process worker (simulates badge printer)
    → BRPOP job
    → simulate print delay
    → build HMAC-signed callback (t=...,v1=...)
    → verify signature (same rules as external webhook)
    → status = checked_in

Kiosk UI
    → polls /attendees
    → shows Not checked in | Pending (spinner) | Checked in
External vendors can still call POST /webhook with a valid X-Signature header.

Journey (how this project evolved)

PhaseFocus1Core HMAC generate/verify, timing-safe compare, unit tests2Warehouse-style sender + /webhook receiver3Modern signature format: t=<timestamp>,v1=<hmac> + replay window4Pivot: Solstice async check-in, Redis queue, pending UI5Kiosk UI, QR codes, admin reset, HTTPS deploy on Render

Features

Async check-in (pending until print confirmation)
Redis job queue
HMAC-SHA256 callbacks with timestamp / replay protection
Timing-safe comparison (hmac.compare_digest)
Duplicate scan protection (HTTP 409)
Safe handling of late/duplicate callbacks (only pending → checked_in)
Kiosk UI with status colours and pending spinner
On-page QR codes for ATT-001 / ATT-002 / ATT-003
POST /admin/reset for demo re-runs
Public HTTPS deployment (Render free tier; worker runs in-process)


Project structure
texthmac-prototype/
├── app.py              # FastAPI: check-in, webhook, worker thread, kiosk
├── attendees.py        # Redis attendee state + print queue
├── hmac_service.py     # HMAC helpers + modern verify
├── sender.py           # Optional standalone printer worker (local)
├── static/
│   ├── index.html      # Kiosk UI
│   └── qrcodes/        # ATT-001/002/003 QR images
├── test_hmac.py
├── test_e2e.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── Tracker.md

Local setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

sudo systemctl start redis-server   # or redis-server
export HMAC_SECRET=super-secret-key-change-me
export REDIS_URL=redis://localhost:6379/0
export ADMIN_TOKEN=demo-reset-token

uvicorn app:app --reload --port 8000
Open http://127.0.0.1:8000
The printer worker runs inside the web process (thread).
sender.py is optional for local experiments with a separate process.

Demo script (instructor)

Reset state:Bashcurl -X POST https://solstice-checkin.onrender.com/admin/reset \
  -H "X-Admin-Token: demo-reset-token"
Open https://solstice-checkin.onrender.com/
Scan ATT-001 QR (or Check In) → Pending → Checked in
Scan ATT-001 again → already checked in, no second print (409)
Optionally check in ATT-002 / ATT-003

Warm the free-tier app first: curl https://solstice-checkin.onrender.com/health

Main API

MethodPathDescriptionGET/Kiosk UIGET/healthHealth 
checkGET/attendeesList attendees + statusGET/POST/checkin/{id}Start check-in (QR uses GET)POST/webhookHMAC-signed print completion callbackPOST/admin/resetReset attendees + clear queue (X-Admin-Token)GET/docsOpenAPI docs

Signature format (webhook)
textX-Signature: t=<unix_timestamp>,v1=<hmac_hex>
Signed payload: timestamp.body
Rejected if missing header, bad signature, or timestamp outside ±5 minutes.

Environment variables

VariablePurposeHMAC_SECRETShared secret for signaturesREDIS_URLRedis connection stringTOLERANCE_SECONDSReplay window (default 300)PRINT_DELAY_SECONDSSimulated print latency (default 2)ADMIN_TOKENToken for /admin/reset
Never commit .env.

Security notes

Timing-safe HMAC compare
Timestamp-based replay protection
Secret only in environment variables
Duplicate check-in does not enqueue another print job
Callbacks only promote pending → checked_in


Deploy notes (Render)

Free Web Service only (Background Workers are paid)
Printer logic runs in-process on startup
Redis via Key Value or Upstash (REDIS_URL)
Free tier may sleep; hit /health before a live demo


Tests
Bashpython -m pytest -v --cov=hmac_service --cov-report=term-missing

What we would improve with more time

Separate worker process in production
Persistent audit log of scans and callbacks
Real vendor webhook integration tests
Stronger admin authentication (e.g. OAuth)
Alignment with the Standard Webhooks specification