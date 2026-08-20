# app.py
import os
import logging
import json
import threading
import time
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from hmac_service import verify_signed_request
from attendees import (
    seed_attendees, get_attendee, set_attendee, list_attendees,
    enqueue_print_job, STATUS_NOT, STATUS_PENDING, STATUS_CHECKED
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

PRINT_DELAY_SECONDS = float(os.getenv("PRINT_DELAY_SECONDS", "2"))
logger = logging.getLogger("solstice")

app = FastAPI(title="Solstice Events – Check-in Kiosk", version="1.0.0")

SECRET = os.getenv("HMAC_SECRET")
if not SECRET:
    raise RuntimeError("HMAC_SECRET is required")
SECRET_KEY = SECRET.encode()
TOLERANCE = int(os.getenv("TOLERANCE_SECONDS", "300"))

# Seed on startup
def finalize_checkin(attendee_id: str, source: str = "webhook"):
    """Promote pending → checked_in. Safe if called more than once."""
    att = get_attendee(attendee_id)
    if not att:
        logger.warning(f"FINALIZE | attendee not found: {attendee_id}")
        return False

    if att["status"] == STATUS_PENDING:
        att["status"] = STATUS_CHECKED
        set_attendee(att)
        logger.info(f"ACCEPTED | {attendee_id} marked checked_in (via {source})")
        return True

    logger.info(f"IGNORED | callback for {attendee_id} in status {att['status']} (via {source})")
    return False

@app.get("/checkin/{attendee_id}")
def checkin_get(attendee_id: str):
    return checkin(attendee_id)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/attendees")
def attendees():
    return {"attendees": list_attendees()}

@app.get("/attendees/{attendee_id}")
def attendee_detail(attendee_id: str):
    att = get_attendee(attendee_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return att

def printer_worker_loop():
    """Simulates the badge-printer vendor: dequeue → print → signed callback handling."""
    from hmac_service import create_signature_header, verify_signed_request
    from attendees import pop_print_job

    logger.info("Printer worker thread started (in-process)")
    while True:
        try:
            attendee_id = pop_print_job(timeout=5)
            if not attendee_id:
                continue

            logger.info(f"WORKER | printing badge for {attendee_id}")
            time.sleep(PRINT_DELAY_SECONDS)

            body = json.dumps(
                {"attendee_id": attendee_id, "result": "success"},
                separators=(",", ":"),
                sort_keys=True,
            )
            signature = create_signature_header(SECRET, body)

            is_valid, reason = verify_signed_request(
                key=SECRET_KEY,
                body=body,
                signature_header=signature,
                tolerance_seconds=TOLERANCE,
            )
            if not is_valid:
                logger.warning(f"WORKER | simulated callback failed verification: {reason}")
                continue

            finalize_checkin(attendee_id, source="worker")
        except Exception as e:
            logger.error(f"WORKER | error: {e}")
            time.sleep(1)

@app.post("/checkin/{attendee_id}")
def checkin(attendee_id: str):
    att = get_attendee(attendee_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attendee not found")

    if att["status"] == STATUS_CHECKED:
        logger.warning(f"DUPLICATE | {attendee_id} already checked in – no print job")
        raise HTTPException(
            status_code=409,
            detail="Attendee already checked in. No second badge will be printed."
        )

    if att["status"] == STATUS_PENDING:
        return {
            "status": "pending",
            "message": "Print job already in progress",
            "attendee": att
        }

    # New check-in → pending + enqueue
    att["status"] = STATUS_PENDING
    set_attendee(att)
    enqueue_print_job(attendee_id)
    logger.info(f"ENQUEUED | print job for {attendee_id}")

    return {
        "status": "pending",
        "message": "Check-in started. Waiting for badge printer confirmation.",
        "attendee": att
    }

@app.post("/webhook")
async def webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
):
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    if not x_signature:
        logger.warning("REJECTED | Missing X-Signature header")
        raise HTTPException(status_code=401, detail="Missing X-Signature header")

    is_valid, reason = verify_signed_request(
        key=SECRET_KEY,
        body=body_str,
        signature_header=x_signature,
        tolerance_seconds=TOLERANCE,
    )
    if not is_valid:
        logger.warning(f"REJECTED | {reason}")
        raise HTTPException(status_code=401, detail=reason)

    try:
        payload = json.loads(body_str)
        attendee_id = payload.get("attendee_id")
        result = payload.get("result")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid callback payload")

    if result != "success" or not attendee_id:
        raise HTTPException(status_code=400, detail="Invalid print result")

    finalize_checkin(attendee_id, source="webhook")
    return {"status": "ok", "attendee_id": attendee_id}
@app.on_event("startup")
def on_startup():
    seed_attendees()
    t = threading.Thread(target=printer_worker_loop, daemon=True)
    t.start()


@app.get("/")
def kiosk():
    return FileResponse("static/index.html")