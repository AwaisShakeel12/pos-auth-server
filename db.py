import os
from supabase import create_client

_client = None
TABLE = "licenses"

def get_db():
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    return _client

def normalize_key(k):
    return (k or "").strip().upper()

def find_license(key):
    r = get_db().table(TABLE).select("*").eq("license_key", normalize_key(key)).execute()
    return r.data[0] if r.data else None

def create_license(key, customer):
    r = get_db().table(TABLE).insert({
        "license_key": normalize_key(key),
        "customer_name": customer.strip(),
        "status": "UNUSED",
        "fingerprint": None,
        "activated_at": None,
    }).execute()
    return r.data[0]

def update_license(key, fields):
    r = get_db().table(TABLE).update(fields).eq("license_key", normalize_key(key)).execute()
    return r.data[0] if r.data else None

def list_licenses():
    r = get_db().table(TABLE).select("*").order("created_at", desc=True).execute()
    return r.data