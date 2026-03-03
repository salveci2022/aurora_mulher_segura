from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import base64

v = Vapid.from_file("private_key.pem")

# ===== PUBLIC KEY =====
public_key_bytes = v.public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

public_key = base64.urlsafe_b64encode(public_key_bytes).decode("utf-8").rstrip("=")

# ===== PRIVATE KEY =====
private_key_bytes = v.private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

private_key = base64.urlsafe_b64encode(private_key_bytes).decode("utf-8").rstrip("=")

print("\n=== VAPID KEYS CORRETAS ===\n")
print("PUBLIC KEY (vai no JavaScript):")
print(public_key)
print("\nPRIVATE KEY (vai no Flask):")
print(private_key)
print("\n===========================\n")