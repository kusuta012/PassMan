from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from backend.core.auth import create_vault, unlock_vault, lock_vault, vault_exists
from backend.core.vault import add_entry, update_password, update_entry_meta, add_note, update_note
from backend.core.vault import enable_totp, get_totp_code
from backend.core.vault import soft_delete_entry, restore_entry
from backend.core.vault import soft_delete_note, restore_note
from backend.core.vault import detect_password_reuse, entries_needing_rotation
from backend.utils.password_gen import generate_password
from backend.utils.strength import check_strength
from fastapi.responses import JSONResponse

app = FastAPI()
templates = Jinja2Templates(directory="backend/templates")

app.mount("/static", StaticFiles(directory="backend/static"), name="static")

MASTER_KEY = None
VAULT = None 

def autosave():
    global VAULT, MASTER_KEY
    if VAULT is not None and MASTER_KEY is not None:
        lock_vault(VAULT, MASTER_KEY)

@app.get("/", response_class=HTMLResponse)
def lock_screen(request: Request):
    return templates.TemplateResponse(
        "lock.html",
        {"request": request, "error": None }
        )
    
@app.post("/")
def unlock(request: Request, master: str = Form(...)):
    global MASTER_KEY, VAULT
    
    try: 
        if not vault_exists():
            create_vault(master)
            
        VAULT = unlock_vault(master)
        MASTER_KEY = master
        
        return RedirectResponse("/dashboard", status_code=302)
    
    except Exception as e:
        return templates.TemplateResponse(
            "lock.html",
            {"request": request, "error": str(e)}
        )
        
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request,
            "entries": VAULT["entries"],
            "notes": VAULT["notes"]
        }
    )
    
@app.get("/lock")
def lock():
    global MASTER_KEY, VAULT
    
    if VAULT and MASTER_KEY:
        lock_vault(VAULT, MASTER_KEY)
        
    VAULT = None
    MASTER_KEY = None
    return RedirectResponse("/", status_code=302)

@app.get("/add")
def add_password_page(request: Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse(
        "add_entry.html",
        {"request": request, "error": None}
    )

@app.post("/add")
def add_password(
    request: Request,
    site: str = Form(...),
    username: str = Form(""),
    password: str = Form(""),
    tags: str = Form("")
    
):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    try: 
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        strength = check_strength(password)
        
        if strength["score"] < 2:
            return templates.TemplateResponse(
            "add_entry.html",
            {
                "request": request,
                "error": "this password is too weak , please use a stronger one",
                "site": site,
                "username": username,
                "tags": tags
            }
        )
        
        reuse = detect_password_reuse(VAULT)
        for a, b in reuse:
            if password == a["password"]:
                return templates.TemplateResponse(
                    "add_entry.html",
                    {
                        "request": request,
                        "error": "this password is already used for anothe entry",
                        "site": site,
                        "username": username,
                        "tags": tags
                    }
                )
            
        add_entry(VAULT, site, username, password, tag_list)
        autosave()
        return RedirectResponse("/dashboard", status_code=302)
    
    except Exception as e:
        return templates.TemplateResponse(
            "add_entry.html",
            {
                "request": request,
                "error": str(e),
                "site": site,
                "username": username,
                "tags": tags
            }
        )

@app.get("/add-note", response_class=HTMLResponse)
def add_note_page(request: Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse(
        "add_note.html",
        {"request": request, "error": None}
        )


@app.post("/add-note")
def save_note(request: Request, title: str = Form(...), content: str = Form(...), tags: str = Form("")):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    try:
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        add_note(VAULT, title, content, tag_list)
        autosave()
        return RedirectResponse("/dashboard", status_code=302)
    
    except Exception as e:
        return templates.TemplateResponse(
            "add_note.html",
            {"request": request, "error": str(e), "title": title, "content": content, "tags": tags}
        )

@app.get("/generate")
def generate(
    length: int = Query(16, ge=8, le=64),
    upper: bool = Query(False),
    lower: bool = Query(False),
    digits: bool = Query(False),
    symbols: bool = Query(False),
):
    
    if not any([upper, lower, digits, symbols]):
        upper = lower = digits = symbols = True
        
    pwd = generate_password(
        length=length,
        use_upper=upper,
        use_lower=lower,
        use_digits=digits,
        use_symbols=symbols
    )
    return JSONResponse({"password": pwd})

@app.get("/generator", response_class=HTMLResponse)
def generator_page(request: Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("generator.html", {"request": request}) 

@app.get("/totp/{entry_id}", response_class=HTMLResponse)
def totp_page(entry_id: str, request:Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    entry = next((e for e in VAULT["entries"] if e["id"] == entry_id), None)
    if not entry:
        return RedirectResponse("/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "totp.html",
        {"request": request, "entry": entry}
    )
    
@app.post("/totp/{entry_id}")
def enable_totp_route(
    entry_id: str,
    secret: str = Form(...)
):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    enable_totp(VAULT, entry_id, secret)
    autosave()
    
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/totp-code/{entry_id}")
def totp_code_api(entry_id: str):
    if not VAULT:
        return {"error": "locked"}
    
    code = get_totp_code(VAULT, entry_id)
    return {"code": code}

@app.post("/delete/{entry_id}")
def delete_entry(entry_id: str):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    soft_delete_entry(VAULT, entry_id)
    autosave()
    return RedirectResponse("/dashboard", status_code=302)

@app.post("/restore/{entry_id}")
def restore_entry_route(entry_id: str):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    restore_entry(VAULT, entry_id)
    autosave()
    return RedirectResponse("/trash", status_code=302)

@app.get("/trash", response_class=HTMLResponse)
def trash_page(request: Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    return templates.TemplateResponse("trash.html", {"request": request, "trash": VAULT["trash"]})

@app.post("/trash/clear")
def clear_trash():
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    VAULT["trash"].clear()
    autosave()
    return RedirectResponse("/trash", status_code=302)

@app.get("/edit/{entry_id}", response_class=HTMLResponse)
def entry_edit_page(entry_id: str, request:Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    entry = next((e for e in VAULT["entries"] if e["id"] == entry_id), None)
    if not entry:
        return RedirectResponse("/dashboard", status_code=302)
    
    return templates.TemplateResponse("edit_entry.html", {"request": request, "entry": entry})
        
@app.post("/edit/{entry_id}")
def save_entry_meta(
    entry_id: str,
    site: str = Form(...),
    username: str = Form(""),
    tags: str = Form("")
):
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    update_entry_meta(VAULT, entry_id, site, username, tag_list)
    autosave()
    return RedirectResponse("/dashboard", status_code=302)


@app.post("/change-password/{entry_id}")
def change_password(
    entry_id: str,
    new_password: str = Form(...)
):
    if VAULT is None:
        return RedirectResponse("/", status_code=302)
    
    try:
        strength = check_strength(new_password)
        if strength["score"] < 2:
            return "this paasword is too weak, use a stronger one"
        update_password(VAULT, entry_id, new_password)
        autosave()
        return RedirectResponse("/dashboard", status_code=302)
    except ValueError as e:
        return str(e)

@app.get("/edit-note/{note_id}", response_class=HTMLResponse)
def edit_note_page(note_id: str, request: Request):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    note = next((n for n in VAULT["notes"] if n["id"] == note_id), None)
    if not note:
        return RedirectResponse("/dashboard", status_code=302)

    return templates.TemplateResponse(
        "edit_note.html",
        {"request": request, "note": note}
    )

@app.post("/edit-note/{note_id}")
def save_new_note(note_id: str, title: str = Form(...), content: str = Form(...), tags: str = Form("")):
    if not VAULT:
        return RedirectResponse("/", status_code=302)
    
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    update_note(VAULT, note_id, title, content, tag_list)
    autosave()
    return RedirectResponse("/dashboard", status_code=302)

@app.post("/delete-note/{note_id}")
def delete_note(note_id: str):
    if VAULT is None:
        return RedirectResponse("/", status_code=302)

    soft_delete_note(VAULT, note_id)
    autosave()
    return RedirectResponse("/dashboard", status_code=302)

@app.post("/restore-note/{note_id}")
def restore_note_route(note_id: str):
    if VAULT is None:
        return RedirectResponse("/", status_code=302)

    restore_note(VAULT, note_id)
    autosave()
    return RedirectResponse("/trash", status_code=302)
