import secrets
import hashlib

def generate_reset_token() -> str:
    return secrets.token_urlsafe(48)  # largo y seguro

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
