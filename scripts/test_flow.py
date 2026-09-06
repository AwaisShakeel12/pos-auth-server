import requests, json
BASE = "http://127.0.0.1:8000"
ADMIN = "awais12feb@C53"   # must match ADMIN_PASSWORD in .env

tok = requests.post(f"{BASE}/admin/login", json={"password": ADMIN}).json()["token"]
H = {"Authorization": f"Bearer {tok}"}

key = requests.post(f"{BASE}/admin/licenses/create", json={"customer_name": "Fahad Medical Store"}, headers=H).json()["license"]["license_key"]
print("Created:", key)

r = requests.post(f"{BASE}/activate", json={"license_key": key, "fingerprint": "PC-AAA"})
print("First activate :", r.status_code, r.json().get("customer"))

r = requests.post(f"{BASE}/activate", json={"license_key": key, "fingerprint": "PC-AAA"})
print("Same machine   :", r.status_code)

r = requests.post(f"{BASE}/activate", json={"license_key": key, "fingerprint": "PC-BBB"})
print("Other machine  :", r.status_code, r.json().get("detail"))

requests.post(f"{BASE}/admin/licenses/reset", json={"license_key": key}, headers=H)
r = requests.post(f"{BASE}/activate", json={"license_key": key, "fingerprint": "PC-BBB"})
print("Reset+new PC   :", r.status_code)

requests.post(f"{BASE}/admin/licenses/disable", json={"license_key": key}, headers=H)
r = requests.post(f"{BASE}/activate", json={"license_key": key, "fingerprint": "PC-BBB"})
print("Disabled       :", r.status_code, r.json().get("detail"))

requests.post(f"{BASE}/admin/licenses/enable", json={"license_key": key}, headers=H)
r = requests.post(f"{BASE}/activate", json={"license_key": key, "fingerprint": "PC-BBB"})
print("Re-enabled     :", r.status_code)

print(json.dumps(requests.get(f"{BASE}/admin/licenses", headers=H).json(), indent=2))