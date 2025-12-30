import hmac
import hashlib

def compute_hmac(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()

def verify_hmac(key: bytes, data:bytes, expected: bytes) -> bool:
    return hmac.compare_digest(
        compute_hmac(key, data),
        expected
    )