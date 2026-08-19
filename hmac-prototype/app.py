# app.py
import os
import logging
from fastapi import FastAPI, Request, HTTPException, Header

from hmac_service import verify_signed_request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("webhook")

app = FastAPI(
    title="Modern Webhook Signature Verification",
    description="HMAC-SHA256 verification with timestamp-based replay protection",
    version="2.0.0"
)

SECRET = os.getenv("HMAC_SECRET")
if not SECRET:
    raise RuntimeError("HMAC_SECRET environment variable is required")
SECRET_KEY = SECRET.encode()

# Simple in-memory log of accepted events (optional, for demo visibility)
RECENT_EVENTS = []

@app.get("/health")
def health():
    return {"status": "ok"}

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
        tolerance_seconds=300   # 5 minutes
    )

    if not is_valid:
        logger.warning(f"REJECTED | {reason} | header={x_signature[:40]}...")
        raise HTTPException(status_code=401, detail=reason)

    # Valid request
    logger.info("ACCEPTED | Valid signature")
    RECENT_EVENTS.append({
        "body_preview": body_str[:120],
        "signature": x_signature
    })
    # keep only last 20
    if len(RECENT_EVENTS) > 20:
        RECENT_EVENTS.pop(0)

    return {
        "status": "accepted",
        "message": "Signature verified successfully"
    }

@app.get("/events")
def list_recent_events():
    """Optional simple visibility into accepted events"""
    return {"recent_events": RECENT_EVENTS}