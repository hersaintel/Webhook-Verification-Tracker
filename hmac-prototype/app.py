# app.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from hmac_service import generate_hmac, verify_hmac

app = FastAPI(
    title="HMAC Prototype",
    description="Simple service that signs and verifies HMACs",
    version="1.0.0"
)

# Load secret from environment variable (never hard-code in real projects)
SECRET_KEY = os.getenv("HMAC_SECRET", "super-secret-key-change-me").encode()

class SignRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message to sign")

class SignResponse(BaseModel):
    hmac: str

class VerifyRequest(BaseModel):
    message: str = Field(..., min_length=1)
    hmac: str = Field(..., min_length=1)

class VerifyResponse(BaseModel):
    valid: bool

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/sign", response_model=SignResponse)
def sign(req: SignRequest):
    tag = generate_hmac(SECRET_KEY, req.message)
    return {"hmac": tag}

@app.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest):
    is_valid = verify_hmac(SECRET_KEY, req.message, req.hmac)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid HMAC")
    return {"valid": True}