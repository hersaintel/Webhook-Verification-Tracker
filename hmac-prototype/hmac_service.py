# hmac_service.py
import hmac
import hashlib
import time
from typing import Union, Optional, Tuple

def generate_hmac(
    key: Union[str, bytes],
    message: Union[str, bytes],
    algorithm: str = "sha256"
) -> str:
    if isinstance(key, str):
        key = key.encode()
    if isinstance(message, str):
        message = message.encode()

    digestmod = getattr(hashlib, algorithm)
    return hmac.new(key, message, digestmod).hexdigest()

def verify_hmac(
    key: Union[str, bytes],
    message: Union[str, bytes],
    received_hmac: str,
    algorithm: str = "sha256"
) -> bool:
    expected = generate_hmac(key, message, algorithm)
    return hmac.compare_digest(expected, received_hmac)

def create_signature_header(
    key: Union[str, bytes],
    body: str,
    algorithm: str = "sha256"
) -> str:
    """
    Creates a modern signature header value:
    t=<timestamp>,v1=<hmac>
    """
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{body}"
    signature = generate_hmac(key, signed_payload, algorithm)
    return f"t={timestamp},v1={signature}"

def parse_signature_header(header: str) -> Optional[Tuple[str, str]]:
    """
    Parses 't=1712345678,v1=abcdef...' 
    Returns (timestamp, signature) or None if invalid format.
    """
    try:
        parts = dict(item.split("=", 1) for item in header.split(","))
        timestamp = parts.get("t")
        signature = parts.get("v1")
        if timestamp and signature:
            return timestamp, signature
    except Exception:
        pass
    return None

def verify_signed_request(
    key: Union[str, bytes],
    body: str,
    signature_header: str,
    tolerance_seconds: int = 300,   # 5 minutes
    algorithm: str = "sha256"
) -> Tuple[bool, str]:
    """
    Full modern verification.
    Returns (is_valid, reason)
    """
    parsed = parse_signature_header(signature_header)
    if not parsed:
        return False, "Invalid signature header format"

    timestamp_str, received_signature = parsed

    try:
        timestamp = int(timestamp_str)
    except ValueError:
        return False, "Invalid timestamp"

    now = int(time.time())
    if abs(now - timestamp) > tolerance_seconds:
        return False, "Timestamp outside allowed tolerance (possible replay)"

    signed_payload = f"{timestamp_str}.{body}"
    if not verify_hmac(key, signed_payload, received_signature, algorithm):
        return False, "Invalid signature"

    return True, "Valid"