# attendees.py
import json
import redis
import os
from typing import Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=None,   # important: allow blocking commands like BRPOP
)

# Seed data (at least 3 attendees)
SEED = {
    "ATT-001": {"id": "ATT-001", "name": "Alex Rivera", "status": "not_checked_in"},
    "ATT-002": {"id": "ATT-002", "name": "Jordan Lee", "status": "not_checked_in"},
    "ATT-003": {"id": "ATT-003", "name": "Sam Okonkwo", "status": "not_checked_in"},
}

STATUS_NOT = "not_checked_in"
STATUS_PENDING = "pending"
STATUS_CHECKED = "checked_in"

def seed_attendees():
    for att_id, data in SEED.items():
        key = f"attendee:{att_id}"
        if not r.exists(key):
            r.set(key, json.dumps(data))

def get_attendee(attendee_id: str) -> Optional[dict]:
    raw = r.get(f"attendee:{attendee_id}")
    if not raw:
        return None
    return json.loads(raw)

def set_attendee(attendee: dict):
    r.set(f"attendee:{attendee['id']}", json.dumps(attendee))

def list_attendees() -> list:
    keys = r.keys("attendee:*")
    result = []
    for key in keys:
        raw = r.get(key)
        if raw:
            result.append(json.loads(raw))
    return sorted(result, key=lambda x: x["id"])

def enqueue_print_job(attendee_id: str):
    r.lpush("print_queue", attendee_id)

def pop_print_job(timeout: int = 5):
    try:
        item = r.brpop("print_queue", timeout=timeout)
        if item:
            return item[1]
    except redis.exceptions.TimeoutError:
        # Socket timeout – treat as "no job" and keep looping
        return None
    except redis.exceptions.ConnectionError as e:
        print(f"[redis] connection error: {e}")
        return None
    return None