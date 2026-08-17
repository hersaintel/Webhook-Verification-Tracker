#!/usr/bin/env python3
"""
Fake Warehouse Sender
--------------------
Simulates a warehouse system that sends an order notification
with an HMAC signature in the header.
"""

import json
import os
import sys
from datetime import datetime, timezone

import httpx
from hmac_service import generate_hmac

# Configuration
SECRET = os.getenv("HMAC_SECRET", "super-secret-key-change-me")
RECEIVER_URL = os.getenv("RECEIVER_URL", "http://127.0.0.1:8000/webhook")
ALGORITHM = "sha256"

def build_payload() -> dict:
    """Create a realistic fake warehouse payload."""
    return {
        "event": "order.shipped",
        "order_id": "ORD-2026-88421",
        "warehouse": "WH-EAST-03",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "items": [
            {"sku": "SKU-1001", "qty": 2},
            {"sku": "SKU-2044", "qty": 1},
        ],
        "status": "shipped"
    }

def main():
    # 1. Build the payload
    payload = build_payload()

    # 2. Serialize to JSON (canonical form matters!)
    #    We use separators=(",", ":") so there are no extra spaces.
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    # 3. Generate HMAC of the raw body
    signature = generate_hmac(SECRET, body, algorithm=ALGORITHM)

    # 4. Prepare headers
    headers = {
        "Content-Type": "application/json",
        "X-HMAC-Signature": signature,          # ← the important header
        "X-HMAC-Algorithm": ALGORITHM,
        "User-Agent": "WarehouseSender/1.0"
    }

    print("=== Fake Warehouse Sender ===")
    print(f"Target URL : {RECEIVER_URL}")
    print(f"Algorithm  : {ALGORITHM}")
    print(f"Signature  : {signature}")
    print(f"Body       : {body}")
    print("-" * 50)

    # 5. Send the real HTTP POST
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(RECEIVER_URL, content=body, headers=headers)

        print(f"Status code : {response.status_code}")
        print(f"Response    : {response.text}")

        if response.status_code == 200:
            print("\n✅ Request accepted by receiver")
        else:
            print("\n❌ Request rejected by receiver")

    except httpx.ConnectError:
        print("\n  Could not connect to the receiver.")
        print("   Make sure the FastAPI server is running:")
        print("   uvicorn app:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()