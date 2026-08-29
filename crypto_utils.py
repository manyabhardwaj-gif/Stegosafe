import base64
from Crypto.Cipher import AES, ChaCha20_Poly1305
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes


def derive_key(password, salt):
    return PBKDF2(password.encode('utf-8'), salt,
                  dkLen=32, count=200_000, hmac_hash_module=SHA256)


# ── kept for backward compatibility ──────────────────────────────
def encrypt_message(plaintext, password):
    salt = get_random_bytes(16)
    nonce = get_random_bytes(16)
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    return base64.b64encode(salt + nonce + tag + ct).decode('utf-8')


def decrypt_message(bundle, password):
    b = base64.b64decode(bundle)
    salt, nonce, tag, ct = b[:16], b[16:32], b[32:48], b[48:]
    key = derive_key(password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag).decode('utf-8')


# ── NEW: Double encryption ────────────────────────────────────────
def double_encrypt(plaintext, password1, password2):
    """
    Inner lock  → AES-256-GCM     (password1)
    Outer lock  → ChaCha20-Poly1305 (password2)
    Both needed to read. Either wrong = total failure.
    """
    # Layer 1 — AES
    salt1  = get_random_bytes(16)
    nonce1 = get_random_bytes(16)
    key1   = derive_key(password1, salt1)
    c1     = AES.new(key1, AES.MODE_GCM, nonce=nonce1)
    ct1, tag1 = c1.encrypt_and_digest(plaintext.encode('utf-8'))
    inner = salt1 + nonce1 + tag1 + ct1          # pack layer 1

    # Layer 2 — ChaCha20
    salt2  = get_random_bytes(16)
    nonce2 = get_random_bytes(12)                # ChaCha needs 12 bytes
    key2   = derive_key(password2, salt2)
    c2     = ChaCha20_Poly1305.new(key=key2, nonce=nonce2)
    ct2, tag2 = c2.encrypt_and_digest(inner)
    outer  = salt2 + nonce2 + tag2 + ct2         # pack layer 2

    return base64.b64encode(outer).decode('utf-8')


def double_decrypt(bundle, password1, password2):
    """Peel layer 2 first, then layer 1."""
    b = base64.b64decode(bundle)

    # Peel layer 2 — ChaCha20
    salt2  = b[:16]
    nonce2 = b[16:28]
    tag2   = b[28:44]
    ct2    = b[44:]
    key2   = derive_key(password2, salt2)
    c2     = ChaCha20_Poly1305.new(key=key2, nonce=nonce2)
    inner  = c2.decrypt_and_verify(ct2, tag2)    # fails if p2 wrong

    # Peel layer 1 — AES
    salt1  = inner[:16]
    nonce1 = inner[16:32]
    tag1   = inner[32:48]
    ct1    = inner[48:]
    key1   = derive_key(password1, salt1)
    c1     = AES.new(key1, AES.MODE_GCM, nonce=nonce1)
    return c1.decrypt_and_verify(ct1, tag1).decode('utf-8')  # fails if p1 wrong