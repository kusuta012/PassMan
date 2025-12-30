from typing import Dict, Any , List
from datetime import datetime 
from uuid import uuid4

def new_vault() -> Dict[str, Any]:
    return {
        "entries": [],
        "notes": [],
        "trash": []
    }
    
def new_entry(
    site: str,
    username: str,
    password: str,
    tags: List[str] | None = None
) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    
    return {
        "id": str(uuid4()),
        "site": site,
        "username": username,
        "password": password,
        "password_history": [],
        "tags": tags or [],
        "totp": {
            "enabled": False,
            "secret": None
            
        },
        "rotation_days": 180,
        "created_at": now,
        "updated_at": now,
    }
    
def new_note(
    title: str,
    content: str,
    tags: List[str] | None = None
) -> Dict[str, Any]:
    now = datetime.utcnow().isoformat()
    
    return {
        "id": str(uuid4()),
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": now,
        "updated_at": now,
    }