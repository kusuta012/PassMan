import pyotp
from datetime import datetime
from datetime import datetime, timedelta
from backend.core.schema import new_entry, new_note

def add_entry(vault: dict, site: str, username: str, password: str, tags=None):
    entry = new_entry(site, username, password, tags)
    vault["entries"].append(entry)
    return entry

def add_note(vault: dict, title: str, content: str, tags=None):
    note = new_note(title, content, tags)
    vault["notes"].append(note)
    return note


def delete_entry(vault: dict, entry_id: str):
    entries = vault["entries"]
    for i, entry in enumerate(entries):
        if entry["id"] == entry_id:
            return entries.pop(i)

    raise ValueError("Entry not found")

def soft_delete_entry(vault: dict, entry_id: str):
    from datetime import datetime

    for i, entry in enumerate(vault["entries"]):
        if entry["id"] == entry_id:
            entry["deleted_at"] = datetime.utcnow().isoformat()
            vault.setdefault("trash", []).append(entry)
            return vault["entries"].pop(i)

    raise ValueError("Entry not found")



def restore_entry(vault: dict, entry_id: str):
    for i, entry in enumerate(vault["trash"]):
        if entry["id"] == entry_id:
            entry.pop("deleted_at", None)
            vault["entries"].append(entry)
            return vault["trash"].pop(i)

    raise ValueError("Entry not found in trash")

def list_entries(vault: dict):
    return vault["entries"]


def search_entries(vault: dict, query: str):
    query = query.lower()
    return [
        e for e in vault["entries"]
        if query in e["site"].lower()
        or query in e["username"].lower()
    ]


def detect_password_reuse(vault: dict):
    seen = {}
    reused = []

    for entry in vault["entries"]:
        pwd = entry["password"]
        if pwd in seen:
            reused.append((seen[pwd], entry))
        else:
            seen[pwd] = entry

    return reused


def get_expired_entries(vault: dict, max_age_days: int = 180):
    expired = []
    now = datetime.utcnow()

    for entry in vault["entries"]:
        created = datetime.fromisoformat(entry["created_at"])
        age = now - created

        if age > timedelta(days=max_age_days):
            expired.append({
                "entry": entry,
                "age_days": age.days
            })

    return expired


def needs_rotation(entry: dict) -> bool:
    rotation_days = entry.get("rotation_days", 180)
    updated = datetime.fromisoformat(entry["updated_at"])
    return datetime.utcnow() - updated > timedelta(days=rotation_days)

def entries_needing_rotation(vault: dict):
    return [
        e for e in vault["entries"]
        if needs_rotation(e)
    ]


def enable_totp(vault: dict, entry_id: str, secret: str):
    for entry in vault["entries"]:
        if entry["id"] == entry_id:
            entry["totp"] = {
                "enabled": True,
                "secret": secret
            }
            return entry
    raise ValueError("Entry not found")


def get_totp_code(vault: dict, entry_id: str):
    for entry in vault["entries"]:
        if entry["id"] == entry_id:
            if not entry.get("totp", {}).get("enabled"):
                raise ValueError("TOTP not enabled")

            totp = pyotp.TOTP(entry["totp"]["secret"])
            return totp.now()

    raise ValueError("Entry not found")

def update_password(vault: dict, entry_id: str, new_password: str):
    
    if len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    for entry in vault["entries"]:
        if entry["id"] == entry_id:
            if new_password == entry["password"]:
                raise ValueError("New password must be different")
            
            if new_password in entry.get("password_history", []):
                raise ValueError("Password was used previously")
            
            entry.setdefault("password_history", []).append(entry["password"])
            entry["password"] = new_password
            entry["updated_at"] = datetime.utcnow().isoformat()
            entry["password_history"] = entry["password_history"][-5:]
            
            return entry
        
    raise ValueError("Entry not found")


def update_entry_meta(vault, entry_id, site, username, tags):
    for e in vault["entries"]:
        if e["id"] == entry_id:
            e["site"] = site
            e["username"] = username
            e["tags"] = tags
            e["updated_at"] = datetime.utcnow().isoformat()
            return
    raise ValueError("Entry not found")

def update_note(vault, note_id, title, content, tags):
    for n in vault["notes"]:
        if n["id"] == note_id:
            n["title"] = title
            n["content"] = content
            n["tags"] = tags
            n["updated_at"] = datetime.utcnow().isoformat()
            return
    raise ValueError("Note not found")

def soft_delete_note(vault: dict, note_id: str):
    for i, note in enumerate(vault["notes"]):
        if note["id"] == note_id:
            note["type"] = "note"
            vault["trash"].append(note)
            del vault["notes"][i]
            return
    raise ValueError("Note not found")

def restore_note(vault: dict, note_id: str):
    for i, item in enumerate(vault["trash"]):
        if item["id"] == note_id and item.get("type") == "note":
            vault["notes"].append(item)
            del vault["trash"][i]
            return
    raise ValueError("Note not found in trash")

        
        
def filter_by_tag(vault: dict, tag: str):
    tag = tag.lower()
    return [
        entry for entry in vault["entries"]
        if tag in [t.lower() for t in entry.get("tags", [])]
    ]