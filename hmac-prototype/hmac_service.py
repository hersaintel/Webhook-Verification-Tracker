import hmac
import hashlib
from typing import Union

def generate_hmac(key: Union[str, bytes], message: Union[str, bytes],
                algorithm: str = "sha256") -> str:
    if isinstance(key, str):
        key = key.encode()
    if isinstance(message, str):
        message = message.encode()
    
    digestmod = getattr(hashlib, algorithm)
    return hmac.new(key, message, digestmod).hexdigest()

def verify_hmac(key: Union[str, bytes], message: Union[str, bytes],
                received_hmac: str, algorithm: str = "sha256") -> bool:
    expected = generate_hmac(key, message, algorithm)
    # Constant-time comparison is important
    return hmac.compare_digest(expected, received_hmac)