#!/usr/bin/env python3
"""
Simulated badge-printer vendor worker.
Reads jobs from Redis, "prints", then calls the kiosk webhook with HMAC signature.
"""
import os
import json
import time
import httpx
from dotenv import load_dotenv

from hmac_service import create_signature_header
from attendees import pop_print_job

load_dotenv()

SECRET = os.getenv("HMAC_SECRET", "super-secret-key-change-me")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://127.0.0.1:8000/webhook")
PRINT_DELAY_SECONDS = float(os.getenv("PRINT_DELAY_SECONDS", "2"))

def process_job(attendee_id: str):
    print(f"[worker] Printing badge for {attendee_id} ...")
    time.sleep(PRINT_DELAY_SECONDS)  # simulate printer latency

    body = json.dumps({
        "attendee_id": attendee_id,
        "result": "success"
    }, separators=(",", ":"), sort_keys=True)

    signature = create_signature_header(SECRET, body)
    headers = {
        "Content-Type": "application/json",
        "X-Signature": signature,
        "User-Agent": "BadgePrinterVendor/1.0"
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(WEBHOOK_URL, content=body, headers=headers)
        print(f"[worker] Callback status={resp.status_code} body={resp.text}")
    except Exception as e:
        print(f"[worker] Callback failed: {e}")

def main():
    print("[worker] Badge printer worker started. Waiting for jobs...")
    while True:
        attendee_id = pop_print_job(timeout=5)
        if attendee_id:
            process_job(attendee_id)

if __name__ == "__main__":
    main()