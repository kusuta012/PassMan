import json
import os
from typing import Any, Dict
from backend.core.crypto import (
    generate_salt,
    derive_key,
    encrypt_data,
    decrypt_data
)
from backend.core.schema import new_vault
from backend.core.integrity import compute_hmac, verify_hmac
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
CONFIG_PATH = BASE_DIR / "config.json"
VAULT_PATH = STORAGE_DIR / "vault.enc"
STORAGE_DIR.mkdir(exist_ok=True)


def _load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)


def vault_exists() -> bool:
    return os.path.exists(VAULT_PATH)


def create_vault(master_password: str):
    if vault_exists():
        raise RuntimeError("Vault already exists")

    salt = generate_salt()
    key = derive_key(master_password, salt)

    empty_vault = json.dumps(new_vault()).encode()
    encrypted_vault = encrypt_data(empty_vault, key)

    os.makedirs("storage", exist_ok=True)
    with open(VAULT_PATH, "wb") as f:
        f.write(encrypted_vault)
    
    hmac_value = compute_hmac(key, encrypted_vault)
    
    config = _load_config()
    config["salt"] = salt.hex()
    config["hmac"] = hmac_value.hex()
    _save_config(config)


def unlock_vault(master_password: str) -> Dict[str, Any]:
    if not vault_exists():
        raise RuntimeError("Vault does not exist")

    config = _load_config()

    if not config.get("salt"):
        raise RuntimeError("Vault is corrupted or not initialized (missing salt)")

    salt = bytes.fromhex(config["salt"])
    key = derive_key(master_password, salt)
    stored_hmac = bytes.fromhex(config["hmac"])
    
    with open(VAULT_PATH, "rb") as f:
        encrypted_vault = f.read()

    if not verify_hmac(key, encrypted_vault, stored_hmac):
        raise RuntimeError("Vault integrity check failed")
    
    decrypted = decrypt_data(encrypted_vault, key)
    return json.loads(decrypted.decode())



def lock_vault(vault_data: dict, master_password: str):
    config = _load_config()
    salt = bytes.fromhex(config["salt"])

    key = derive_key(master_password, salt)
    raw = json.dumps(vault_data).encode()
    encrypted = encrypt_data(raw, key)
    hmac_value = compute_hmac(key, encrypted)
    config["hmac"] = hmac_value.hex()
    _save_config(config)

    with open(VAULT_PATH, "wb") as f:
        f.write(encrypted)
