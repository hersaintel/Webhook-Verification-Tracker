import os
import logging
from fastapi import FastAPI, Request, HTTPException, Header
from pydantic import BaseModel
from hmac_service import generate_hmac, verify_hmac

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("webhook")

app = FastAPI(
    title="HMAC Warehouse Receiver",
    description="Receives signed webhooks from the warehouse and verifies HMAC",
    version="1.0.0"
)

# Force secret to be present
SECRET = os.getenv("HMAC_SECRET")
if not SECRET:
    raise RuntimeError(
        "HMAC_SECRET environment variable is required.\n"
        "Example: export HMAC_SECRET='super-secret-key-change-me'"
    )
SECRET_KEY = SECRET.encode()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(
    request: Request,
    x_hmac_signature: str | None = Header(default=None, alias="X-HMAC-Signature"),
    x_hmac_algorithm: str = Header(default="sha256", alias="X-HMAC-Algorithm"),
):
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    # --- Missing header ---
    if not x_hmac_signature:
        logger.warning("REJECTED | Missing X-HMAC-Signature header")
        raise HTTPException(status_code=401, detail="Missing X-HMAC-Signature header")

    # --- Verify signature ---
    is_valid = verify_hmac(
        key=SECRET_KEY,
        message=body_str,
        received_hmac=x_hmac_signature,
        algorithm=x_hmac_algorithm
    )

    if not is_valid:
        logger.warning(
            "REJECTED | Invalid HMAC signature | "
            f"received={x_hmac_signature[:16]}... | body_preview={body_str[:80]}..."
        )
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")

    # Success
    logger.info("ACCEPTED | Valid HMAC signature received")
    return {
        "status": "accepted",
        "message": "HMAC verified successfully"
    }

    """
    Classic webhook-style endpoint.
    - Reads the raw body
    - Verifies the HMAC signature from the header
    - Accepts or rejects
    """

    # 1. Check that the signature header exists
    if not x_hmac_signature:
        raise HTTPException(
            status_code=401,
            detail="Missing X-HMAC-Signature header"
        )

    # 2. Read the raw body (important – we must hash exactly what was sent)
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    # 3. Verify the HMAC (timing-safe)
    is_valid = verify_hmac(
        key=SECRET_KEY,
        message=body_str,
        received_hmac=x_hmac_signature,
        algorithm=x_hmac_algorithm
    )

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid HMAC signature"
        )

    # 4. If we reach here the signature is valid
    #    In a real system you would now process the event
    return {
        "status": "accepted",
        "message": "HMAC verified successfully",
        "received_event": body_str[:200] + ("..." if len(body_str) > 200 else "")
    }