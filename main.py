import os, secrets, string, datetime
from dotenv import load_dotenv

from .server import crypto
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import db
import crypto

app = FastAPI(title="Galaxy POS License Server")

# ---------- models ----------
class ActivateReq(BaseModel):
    license_key: str
    fingerprint: str
class AdminLoginReq(BaseModel):
    password: str
class CreateReq(BaseModel):
    customer_name: str
class KeyReq(BaseModel):
    license_key: str

# ---------- helpers ----------
def gen_license_key():
    alpha = string.ascii_uppercase + string.digits
    return "GP-" + "-".join("".join(secrets.choice(alpha) for _ in range(4)) for _ in range(3))

def require_admin(authorization: str = Header(default="")):
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        raise HTTPException(500, "ADMIN_PASSWORD not configured")
    token = authorization.replace("Bearer ", "").strip()
    if not crypto.verify_admin_token(token, password):
        raise HTTPException(401, "Not authenticated")
    return True

# ---------- public ----------
@app.get("/")
def root():
    return {"ok": True, "service": "Galaxy POS License Server"}

@app.post("/activate")
def activate(req: ActivateReq):
    key = db.normalize_key(req.license_key)
    fp = (req.fingerprint or "").strip().upper()
    if not key or not fp:
        raise HTTPException(400, "license_key and fingerprint are required.")
    lic = db.find_license(key)
    if not lic:
        raise HTTPException(404, "Invalid license key.")
    if lic["status"] == "DISABLED":
        raise HTTPException(403, "License disabled. Contact your seller.")
    if lic["status"] == "ACTIVE":
        if lic["fingerprint"] != fp:
            raise HTTPException(409, "License already activated on another computer. Please contact the seller.")
        # same machine -> just re-issue token (no second binding)
    else:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        lic = db.update_license(key, {"status": "ACTIVE", "fingerprint": fp, "activated_at": now})
    token = crypto.sign_activation_token(lic["license_key"], lic["customer_name"], fp, lic["activated_at"])
    return {"ok": True, "customer": lic["customer_name"], "token": token}

# ---------- admin ----------
@app.post("/admin/login")
def admin_login(req: AdminLoginReq):
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password or not secrets.compare_digest(req.password, password):
        raise HTTPException(401, "Wrong password.")
    return {"ok": True, "token": crypto.make_admin_token(password)}

@app.get("/admin/licenses")
def admin_licenses(_=Depends(require_admin)):
    return db.list_licenses()

@app.post("/admin/licenses/create")
def admin_create(req: CreateReq, _=Depends(require_admin)):
    name = (req.customer_name or "").strip()
    if not name:
        raise HTTPException(400, "Customer name required.")
    key = gen_license_key()
    while db.find_license(key):
        key = gen_license_key()
    return {"ok": True, "license": db.create_license(key, name)}

@app.post("/admin/licenses/reset")
def admin_reset(req: KeyReq, _=Depends(require_admin)):
    if not db.find_license(req.license_key):
        raise HTTPException(404, "License not found.")
    return {"ok": True, "license": db.update_license(req.license_key,
        {"status": "UNUSED", "fingerprint": None, "activated_at": None})}

@app.post("/admin/licenses/disable")
def admin_disable(req: KeyReq, _=Depends(require_admin)):
    if not db.find_license(req.license_key):
        raise HTTPException(404, "License not found.")
    return {"ok": True, "license": db.update_license(req.license_key, {"status": "DISABLED"})}

@app.post("/admin/licenses/enable")
def admin_enable(req: KeyReq, _=Depends(require_admin)):
    lic = db.find_license(req.license_key)
    if not lic:
        raise HTTPException(404, "License not found.")
    # keep machine binding if it exists, otherwise back to UNUSED
    return {"ok": True, "license": db.update_license(req.license_key,
        {"status": "ACTIVE" if lic["fingerprint"] else "UNUSED"})}



from fastapi.responses import HTMLResponse
import pathlib
_BASE = pathlib.Path(__file__).resolve().parent

@app.get("/admin", response_class=HTMLResponse)
def admin_login_page():
    return (_BASE / "admin_login.html").read_text(encoding="utf-8")

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard_page():
    return (_BASE / "admin_dashboard.html").read_text(encoding="utf-8")