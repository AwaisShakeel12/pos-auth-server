import os, json, base64, time, hmac, hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def _private_key():
    hexkey = os.environ.get("LICENSE_PRIVATE_KEY", "")
    if not hexkey:
        raise RuntimeError("LICENSE_PRIVATE_KEY env var not set")
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(hexkey))

def sign_activation_token(license_key, customer, fingerprint, activated_at):
    """Signed token = base64(payload).base64(ed25519-signature). POS verifies with public key only."""
    payload = json.dumps({
        "license_key": license_key,
        "customer": customer,
        "fingerprint": fingerprint,
        "activated_at": activated_at,
    }, sort_keys=True)
    sig = _private_key().sign(payload.encode())
    return base64.b64encode(payload.encode()).decode() + "." + base64.b64encode(sig).decode()

# ---------- stateless admin session token (HMAC, works on serverless) ----------
def make_admin_token(password, ttl=8 * 3600):
    exp = int(time.time()) + ttl
    sig = hmac.new(password.encode(), f"galaxy-admin|{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.b64encode(f"{exp}.{sig}".encode()).decode()

def verify_admin_token(token, password):
    try:
        exp_str, sig = base64.b64decode(token).decode().split(".", 1)
        if int(exp_str) < time.time():
            return False
        expect = hmac.new(password.encode(), f"galaxy-admin|{exp_str}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expect)
    except Exception:
        return False