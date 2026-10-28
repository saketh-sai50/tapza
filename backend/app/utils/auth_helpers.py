import os
import time
import hmac
import hashlib
import json
import base64
from functools import wraps
from flask import request, jsonify, g, current_app

try:
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    # Deterministic fallback using hashlib pbkdf2 if werkzeug is not available
    def generate_password_hash(password: str) -> str:
        salt = os.urandom(16).hex()
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return f"pbkdf2:sha256:100000${salt}${dk.hex()}"

    def check_password_hash(pwhash: str, password: str) -> bool:
        try:
            _, method, iterations, salt, key = pwhash.split("$")
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations))
            return hmac.compare_digest(dk.hex(), key)
        except Exception:
            return False

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, plain_password)

def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding and padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s.encode("utf-8"))

def generate_jwt(payload: dict, secret: str, expires_in_seconds: int = 86400) -> str:
    """Standard JWT HS256 generator implementation without external binary requirement."""
    header = {"typ": "JWT", "alg": "HS256"}
    body = payload.copy()
    now = int(time.time())
    body["iat"] = now
    body["exp"] = now + expires_in_seconds

    enc_header = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    enc_payload = _b64encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{enc_header}.{enc_payload}".encode("utf-8")
    
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    enc_sig = _b64encode(signature)
    return f"{enc_header}.{enc_payload}.{enc_sig}"

def decode_jwt(token: str, secret: str) -> dict:
    """Standard JWT HS256 decoder and verification."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT token segment count")
        
        enc_header, enc_payload, enc_sig = parts
        signing_input = f"{enc_header}.{enc_payload}".encode("utf-8")
        expected_sig = _b64encode(hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest())

        if not hmac.compare_digest(enc_sig, expected_sig):
            raise ValueError("JWT signature verification failed")

        payload = json.loads(_b64decode(enc_payload).decode("utf-8"))
        if "exp" in payload and time.time() > payload["exp"]:
            raise ValueError("JWT token has expired")

        return payload
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid format"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_jwt(token, current_app.config["JWT_SECRET"])
            g.user_id = payload.get("user_id")
            g.role = payload.get("role")
            g.email = payload.get("email")
            g.zone = payload.get("zone")
        except ValueError as err:
            return jsonify({"error": str(err)}), 401

        return f(*args, **kwargs)
    return decorated

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, "role") or g.role not in allowed_roles:
                return jsonify({"error": f"Access denied. Requires one of roles: {', '.join(allowed_roles)}"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
