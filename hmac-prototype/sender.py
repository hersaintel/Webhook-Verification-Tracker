#!/usr/bin/env python3
"""
Simulated Warehouse Sender
Sends a signed webhook using modern signature format:
X-Signature: t=<timestamp>,v1=<hmac>
"""

import json
import os
import sys
from datetime import datetime, timezone

import httpx
from hmac_service import create_signature_header

SECRET = os.getenv("HMAC_SECRET", "super-secret-key-change-me")
RECEIVER_URL = os.getenv("RECEIVER_URL", "http://127.0.0.1:8000/webhook")

def build_payload() -> dict:
    return {
        "event": "order.shipped",
        "order_id": "ORD-2026-88421",
        "warehouse": "WH-EAST-03",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "items": [
            {"sku": "SKU-1001", "qty": 2},
            {"sku": "SKU-2044", "qty": 1}
        ],
        "status": "shipped"
    }

def main():
    payload = build_payload()
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)

    signature_header = create_signature_header(SECRET, body)

    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature_header,
        "User-Agent": "WarehouseSender/2.0"
    }

    print("=== Warehouse Sender (Modern Signature) ===")
    print(f"Target URL : {RECEIVER_URL}")
    print(f"Signature  : {signature_header}")
    print(f"Body       : {body}")
    print("-" * 50)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(RECEIVER_URL, content=body, headers=headers)

        print(f"Status code : {response.status_code}")
        print(f"Response    : {response.text}")

        if response.status_code == 200:
            print("\nRequest accepted")
        else:
            print("\nRequest rejected")

    except httpx.ConnectError:
        print("\nCould not connect to the receiver.")
        print("Start the server with: uvicorn app:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()