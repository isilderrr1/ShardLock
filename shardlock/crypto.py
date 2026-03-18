import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- 1. MATEMATICA DEI CAMPI FINITI (GF(2^8)) ---
# Tabelle pre-computate per moltiplicazione e divisione veloce
# Questo è lo stesso campo usato da AES (Polinomio irriducibile: 0x11D)
_GF256_EXP = [0] * 512
_GF256_LOG = [0] * 256
_x = 1
for i in range(255):
    _GF256_EXP[i] = _GF256_EXP[i + 255] = _x
    _GF256_LOG[_x] = i
    _x = (_x << 1) ^ (0x11D if _x & 0x80 else 0)

def _gf_mul(a, b):
    if a == 0 or b == 0: return 0
    return _GF256_EXP[_GF256_LOG[a] + _GF256_LOG[b]]

def _gf_div(a, b):
    if b == 0: raise ZeroDivisionError()
    if a == 0: return 0
    return _GF256_EXP[_GF256_LOG[a] - _GF256_LOG[b] + 255]

# --- 2. MOTORE CRITTOGRAFICO SIMMETRICO (AES-GCM) ---

def generate_key():
    return AESGCM.generate_key(bit_length=256)

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    return kdf.derive(password.encode())

def encrypt_data(data: bytes, key: bytes) -> tuple[bytes, bytes]:
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce, ciphertext

def decrypt_data(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)

# --- 3. PERSISTENZA FILE (.SLOCK) ---

def encrypt_file(file_path: str, password: str):
    salt = os.urandom(16)
    key = derive_key(password, salt)
    with open(file_path, "rb") as f:
        data = f.read()
    nonce, ciphertext = encrypt_data(data, key)
    output_path = f"{file_path}.slock"
    with open(output_path, "wb") as f:
        f.write(salt)
        f.write(nonce)
        f.write(ciphertext)
    return output_path

def decrypt_file(file_path: str, password: str):
    with open(file_path, "rb") as f:
        salt = f.read(16)
        nonce = f.read(12)
        ciphertext = f.read()
    key = derive_key(password, salt)
    decrypted_data = decrypt_data(ciphertext, key, nonce)
    output_path = file_path.replace(".slock", "") + ".decrypted" 
    with open(output_path, "wb") as f:
        f.write(decrypted_data)
    return output_path

# --- 4. SHAMIR'S SECRET SHARING (GF(2^8)) ---

def split_key(key: bytes, n: int, k: int) -> list[tuple[int, bytes]]:
    """Divide la chiave in n frammenti usando la soglia k."""
    if k > n: raise ValueError("Soglia k non può essere maggiore di n.")
    
    shares = [bytearray() for _ in range(n)]
    for byte in key:
        # Crea polinomio: p(x) = byte ^ a1*x ^ a2*x^2 ... (XOR è l'addizione in GF)
        coeffs = [byte] + [secrets.randbelow(256) for _ in range(k - 1)]
        for i in range(1, n + 1):
            # Valutazione con Metodo di Horner
            v = 0
            for c in reversed(coeffs):
                v = _gf_mul(v, i) ^ c
            shares[i-1].append(v)
            
    return [(i + 1, bytes(s)) for i, s in enumerate(shares)]

def recover_key(shares: list[tuple[int, bytes]], k: int) -> bytes:
    """Ricostruisce la chiave partendo da k frammenti via Lagrange."""
    if len(shares) < k: raise ValueError(f"Servono {k} frammenti.")
    
    recovered = bytearray()
    subset = shares[:k]
    
    for b_idx in range(len(subset[0][1])):
        secret_byte = 0
        for i in range(k):
            xi, yi = subset[i][0], subset[i][1][b_idx]
            li = 1
            for j in range(k):
                if i == j: continue
                xj = subset[j][0]
                # li = li * (0 - xj) / (xi - xj) -> In GF l'addizione/sottrazione è XOR
                li = _gf_mul(li, _gf_div(xj, xi ^ xj))
            secret_byte ^= _gf_mul(yi, li)
        recovered.append(secret_byte)
    return bytes(recovered)