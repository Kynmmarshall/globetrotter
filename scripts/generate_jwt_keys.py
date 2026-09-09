"""Generate the RS256 JWT signing keypair shared by the microservices.

The User Service holds the PRIVATE key and signs access tokens. Every other
service (Itinerary, Recommendation) verifies tokens using only the PUBLIC key,
so they never need the ability to mint tokens themselves.

Writes (idempotent -- skips generation if both files already exist):

  infra/keys/jwt_private_key.pem   (mode 0600 where the OS supports it)
  infra/keys/jwt_public_key.pem

These are LOCAL DEVELOPMENT secrets: infra/keys/*.pem is gitignored. Docker
Compose mounts them into containers at the paths referenced by
JWT_PRIVATE_KEY_PATH / JWT_PUBLIC_KEY_PATH in .env.example. Rotate and manage
real secrets through a proper secrets manager outside local development.

    python scripts/generate_jwt_keys.py
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parent.parent
KEYS_DIR = ROOT / "infra" / "keys"
PRIVATE_KEY_PATH = KEYS_DIR / "jwt_private_key.pem"
PUBLIC_KEY_PATH = KEYS_DIR / "jwt_public_key.pem"


def generate() -> None:
    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    if PRIVATE_KEY_PATH.exists() and PUBLIC_KEY_PATH.exists():
        print(f"Keypair already exists, leaving unchanged: {KEYS_DIR.relative_to(ROOT)}")
        return

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    PRIVATE_KEY_PATH.write_bytes(private_bytes)
    PUBLIC_KEY_PATH.write_bytes(public_bytes)

    if os.name != "nt":
        PRIVATE_KEY_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)

    print(f"Generated RS256 keypair in {KEYS_DIR.relative_to(ROOT)}")
    print(f"  private: {PRIVATE_KEY_PATH.name} (User Service only)")
    print(f"  public:  {PUBLIC_KEY_PATH.name} (all services)")


if __name__ == "__main__":
    generate()
