# Run ONCE:  python scripts/generate_keys.py
# LICENSE_PRIVATE_KEY  -> server env ONLY (never ship)
# POS_PUBLIC_KEY       -> embed in the POS later (Phase 4)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

priv = Ed25519PrivateKey.generate()
print("LICENSE_PRIVATE_KEY=" + priv.private_bytes(
    serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
    serialization.NoEncryption()).hex())
print("POS_PUBLIC_KEY=" + priv.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex())