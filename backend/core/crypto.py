import base64
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken

ITERATIONS = 200_000
KEY_LENGTH = 32
master_password: str = "abc123456789"

def generate_salt() -> bytes:
    return os.urandom(16)

def derive_key(password: str, salt: bytes) -> bytes:
    if not master_password:
        raise ValueError("Master password cannot be empty")
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
    )   
    
    return base64.urlsafe_b64encode(
        kdf.derive(password.encode())
        )
    
def encrypt_data(data: bytes, key: bytes) -> bytes:
    fernet = Fernet(key)
    return fernet.encrypt(data)

def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    fernet = Fernet(key)
    try:
        return fernet.decrypt(encrypted_data)
    except InvalidToken:
        raise ValueError("Invalid master password or corrupted vault")