# app.py
import os
import logging
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
logger = logging.getLogger("solstice")

app = FastAPI(title="Solstice Events – Check-in Kiosk", version="1.0.0")

SECRET = os.getenv("HMAC_SECRET")
if not SECRET:
    raise RuntimeError("HMAC_SECRET is required")
SECRET_KEY = SECRET.encode()
TOLERANCE = int(os.getenv("TOLERANCE_SECONDS", "300"))

# Seed on startup
seed_attendees()

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
        tolerance_seconds=TOLERANCE
    )

    if not is_valid:
        logger.warning(f"REJECTED | {reason}")
        raise HTTPException(status_code=401, detail=reason)

    # Expected callback body: {"attendee_id": "ATT-001", "result": "success"}
    import json
    try:
        payload = json.loads(body_str)
        attendee_id = payload.get("attendee_id")
        result = payload.get("result")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid callback payload")

    if result != "success" or not attendee_id:
        logger.warning(f"REJECTED | Unexpected callback payload: {body_str[:80]}")
        raise HTTPException(status_code=400, detail="Invalid print result")

    att = get_attendee(attendee_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attendee not found")

    # Only promote from pending → checked_in (safe against out-of-order / duplicate callbacks)
    if att["status"] == STATUS_PENDING:
        att["status"] = STATUS_CHECKED
        set_attendee(att)
        logger.info(f"ACCEPTED | {attendee_id} marked checked_in")
    else:
        logger.info(f"IGNORED | callback for {attendee_id} in status {att['status']}")

    return {"status": "ok", "attendee_id": attendee_id}

# Kiosk UI
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def kiosk():
    return FileResponse("static/index.html")