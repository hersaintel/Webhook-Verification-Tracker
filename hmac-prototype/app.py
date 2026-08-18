# app.py
import os
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import secrets

from hmac_service import verify_hmac

# -------------------- Logging --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("webhook")

# -------------------- App & Secret --------------------
app = FastAPI(
    title="Warehouse Self-Service Portal",
    description="Customer self-service + HMAC-protected webhook",
    version="1.1.0"
)

SECRET = os.getenv("HMAC_SECRET")
if not SECRET:
    raise RuntimeError("HMAC_SECRET environment variable is required")
SECRET_KEY = SECRET.encode()

# -------------------- Fake Data --------------------
ORDERS = {
    "ORD-2026-88421": {
        "order_id": "ORD-2026-88421",
        "status": "shipped",
        "warehouse": "WH-EAST-03",
        "total_value": 89.50,
        "items": [
            {"sku": "SKU-1001", "name": "Wireless Mouse", "qty": 2, "unit_price": 24.75},
            {"sku": "SKU-2044", "name": "USB-C Hub", "qty": 1, "unit_price": 40.00}
        ]
    },
    "ORD-2026-77102": {
        "order_id": "ORD-2026-77102",
        "status": "processing",
        "warehouse": "WH-WEST-01",
        "total_value": 149.00,
        "items": [
            {"sku": "SKU-3099", "name": "Mechanical Keyboard", "qty": 1, "unit_price": 149.00}
        ]
    },
    "ORD-2026-90311": {
        "order_id": "ORD-2026-90311",
        "status": "delivered",
        "warehouse": "WH-EAST-03",
        "total_value": 64.50,
        "items": [
            {"sku": "SKU-1001", "name": "Wireless Mouse", "qty": 1, "unit_price": 24.75},
            {"sku": "SKU-2044", "name": "USB-C Hub", "qty": 1, "unit_price": 39.75}
        ]
    }
}

INVENTORY = {
    "SKU-1001": {"name": "Wireless Mouse", "stock": 42, "unit_price": 24.75},
    "SKU-2044": {"name": "USB-C Hub", "stock": 7, "unit_price": 40.00},
    "SKU-3099": {"name": "Mechanical Keyboard", "stock": 0, "unit_price": 149.00}
}

PENDING_RETURNS = []          # returns that need human review
APPROVED_RETURNS = []
REJECTED_RETURNS = []

# -------------------- Simple Admin Auth (simulated Google login) --------------------
security = HTTPBasic()

ADMIN_USERNAME = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASS", "admin123")   # change in real use

def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# -------------------- Models --------------------
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# -------------------- Webhook (HMAC protected) --------------------
@app.post("/webhook")
async def webhook(
    request: Request,
    x_hmac_signature: str | None = Header(default=None, alias="X-HMAC-Signature"),
    x_hmac_algorithm: str = Header(default="sha256", alias="X-HMAC-Algorithm"),
):
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    if not x_hmac_signature:
        logger.warning("REJECTED | Missing X-HMAC-Signature header")
        raise HTTPException(status_code=401, detail="Missing X-HMAC-Signature header")

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

    logger.info("ACCEPTED | Valid HMAC signature received")
    return {"status": "accepted", "message": "HMAC verified successfully"}

# -------------------- Chatbot / Self-service --------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    msg = req.message.lower().strip()

    # Order status
    if "order" in msg or "status" in msg:
        for order_id, order in ORDERS.items():
            if order_id.lower() in msg:
                items_text = ", ".join(
                    f"{i['qty']}x {i['name']}" for i in order["items"]
                )
                return {
                    "reply": (
                        f"Order {order['order_id']}\n"
                        f"Status: {order['status']}\n"
                        f"Warehouse: {order['warehouse']}\n"
                        f"Total value: ${order['total_value']:.2f}\n"
                        f"Items: {items_text}"
                    )
                }
        return {
            "reply": (
                "Order not found. Available demo orders:\n"
                "ORD-2026-88421, ORD-2026-77102, ORD-2026-90311"
            )
        }

    # Inventory
    if "stock" in msg or "inventory" in msg or "available" in msg:
        for sku, item in INVENTORY.items():
            if sku.lower() in msg or item["name"].lower() in msg:
                status = "In stock" if item["stock"] > 0 else "Out of stock"
                return {
                    "reply": (
                        f"{item['name']} ({sku})\n"
                        f"Available: {item['stock']} units\n"
                        f"Status: {status}\n"
                        f"Unit price: ${item['unit_price']:.2f}"
                    )
                }
        return {
            "reply": (
                "Please specify a SKU or product name.\n"
                "Examples: SKU-1001, SKU-2044, SKU-3099"
            )
        }

    # Return request
    if "return" in msg:
        # Try to find an order ID in the message
        target_order = None
        for order_id in ORDERS:
            if order_id.lower() in msg:
                target_order = ORDERS[order_id]
                break

        if not target_order:
            return {
                "reply": (
                    "To request a return, please include the Order ID.\n"
                    "Example: I want to return ORD-2026-88421"
                )
            }

        return_id = str(uuid.uuid4())[:8].upper()
        value = target_order["total_value"]

        record = {
            "id": return_id,
            "order_id": target_order["order_id"],
            "value": value,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "reason": req.message
        }

        if value < 100:
            record["status"] = "auto_approved"
            APPROVED_RETURNS.append(record)
            return {
                "reply": (
                    f"Return request {return_id} for order {target_order['order_id']}\n"
                    f"Value: ${value:.2f}\n"
                    f"Status: Automatically approved (under $100 threshold)\n"
                    f"You will receive further instructions by email."
                )
            }
        else:
            record["status"] = "pending_review"
            PENDING_RETURNS.append(record)
            return {
                "reply": (
                    f"Return request {return_id} for order {target_order['order_id']}\n"
                    f"Value: ${value:.2f}\n"
                    f"Status: Pending human review (value exceeds $100)\n"
                    f"A team member will review your request shortly."
                )
            }

    # Default help
    return {
        "reply": (
            "I can help you with the following:\n\n"
            "• Order status – example: status of ORD-2026-88421\n"
            "• Inventory check – example: stock of SKU-1001\n"
            "• Return request – example: I want to return ORD-2026-88421"
        )
    }

# -------------------- Admin endpoints --------------------
@app.get("/admin/returns")
def list_returns(admin: str = Depends(get_current_admin)):
    return {
        "pending": PENDING_RETURNS,
        "approved": APPROVED_RETURNS,
        "rejected": REJECTED_RETURNS
    }

@app.post("/admin/returns/{return_id}/approve")
def approve_return(return_id: str, admin: str = Depends(get_current_admin)):
    for i, r in enumerate(PENDING_RETURNS):
        if r["id"] == return_id:
            r["status"] = "approved"
            r["reviewed_by"] = admin
            r["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            APPROVED_RETURNS.append(r)
            PENDING_RETURNS.pop(i)
            return {"message": f"Return {return_id} approved"}
    raise HTTPException(status_code=404, detail="Return not found or already processed")

@app.post("/admin/returns/{return_id}/reject")
def reject_return(return_id: str, admin: str = Depends(get_current_admin)):
    for i, r in enumerate(PENDING_RETURNS):
        if r["id"] == return_id:
            r["status"] = "rejected"
            r["reviewed_by"] = admin
            r["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            REJECTED_RETURNS.append(r)
            PENDING_RETURNS.pop(i)
            return {"message": f"Return {return_id} rejected"}
    raise HTTPException(status_code=404, detail="Return not found or already processed")

# -------------------- Static files & pages --------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def customer_home():
    return FileResponse("static/index.html")

@app.get("/admin")
def admin_home():
    return FileResponse("static/admin.html")