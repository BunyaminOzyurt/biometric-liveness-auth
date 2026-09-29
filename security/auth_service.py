import time
import base64
import json
import hmac
import hashlib
import numpy as np

# PyJWT & Cryptography Opsiyonel Import Entegrasyonu (Bulunmazsa Standart Kütüphane Fallback'i)
try:
    import jwt as pyjwt_module
    HAS_PYJWT = True
except ImportError:
    HAS_PYJWT = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def generate_key_from_passphrase(passphrase: str, salt: bytes = b"static_forensic_salt_2026") -> bytes:
    """
    Kullanıcı şifresinden 32-byte Fernet/AES uyumlu anahtar üretir.
    """
    if HAS_CRYPTO:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    else:
        # Standard Library Fallback (PBKDF2 HMAC SHA256)
        key_raw = hashlib.pbkdf2_hmac('sha256', passphrase.encode('utf-8'), salt, 100_000, dklen=32)
        return base64.urlsafe_b64encode(key_raw)


def encrypt_biometric_data(embedding: np.ndarray, secret_key: bytes) -> str:
    """
    128-D biyometrik yüz vektörünü Fernet veya HMAC-XOR ile şifreler.
    """
    data_list = [float(x) for x in embedding.flatten()]
    json_bytes = json.dumps(data_list).encode('utf-8')

    if HAS_CRYPTO:
        fernet = Fernet(secret_key)
        return fernet.encrypt(json_bytes).decode('utf-8')
    else:
        # Standart kütüphane akış şifreleme fallback'i
        key_bytes = hashlib.sha256(secret_key).digest()
        cipher_bytes = bytearray()
        for i, b in enumerate(json_bytes):
            cipher_bytes.append(b ^ key_bytes[i % len(key_bytes)])
        mac = hmac.new(secret_key, cipher_bytes, hashlib.sha256).digest()
        payload = base64.b64encode(mac + cipher_bytes).decode('utf-8')
        return f"ENC_V1_{payload}"


def decrypt_biometric_data(encrypted_str: str, secret_key: bytes) -> np.ndarray:
    """
    Şifrelenmiş metni çözerek 128-D numpy yüz vektörüne dönüştürür.
    """
    if HAS_CRYPTO and not encrypted_str.startswith("ENC_V1_"):
        fernet = Fernet(secret_key)
        decrypted_bytes = fernet.decrypt(encrypted_str.encode('utf-8'))
        data_list = json.loads(decrypted_bytes.decode('utf-8'))
        return np.array(data_list, dtype=np.float32)
    else:
        clean_str = encrypted_str.replace("ENC_V1_", "")
        raw_data = base64.b64decode(clean_str.encode('utf-8'))
        mac_expected, cipher_bytes = raw_data[:32], raw_data[32:]

        mac_actual = hmac.new(secret_key, cipher_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(mac_expected, mac_actual):
            raise ValueError("Biyometrik veri bütünlüğü doğrulanamadı veya Parola Yanlış!")

        key_bytes = hashlib.sha256(secret_key).digest()
        plain_bytes = bytearray()
        for i, b in enumerate(cipher_bytes):
            plain_bytes.append(b ^ key_bytes[i % len(key_bytes)])

        data_list = json.loads(plain_bytes.decode('utf-8'))
        return np.array(data_list, dtype=np.float32)


def generate_secure_jwt(user_id: str, secret_key: str, expires_in_seconds: int = 3600) -> str:
    """
    Başarılı biyometrik doğrulamada kullanılabilecek RFC 7519 Uyumlu JWT Token üretir.
    """
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + expires_in_seconds,
        "auth_method": "biometric_liveness_v1",
        "iss": "forensic_vision_auth"
    }

    if HAS_PYJWT:
        return pyjwt_module.encode(payload, secret_key, algorithm="HS256")
    else:
        # Standart Kütüphane JWT Üretimi (RFC 7519 HMAC-SHA256)
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(secret_key.encode('utf-8'), signing_input, hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_jwt_token(token: str, secret_key: str) -> dict:
    """
    JWT token imzasını ve geçerlilik süresini doğrular.
    """
    if HAS_PYJWT:
        try:
            payload = pyjwt_module.decode(token, secret_key, algorithms=["HS256"], issuer="forensic_vision_auth")
            return {"valid": True, "payload": payload}
        except pyjwt_module.ExpiredSignatureError:
            return {"valid": False, "error": "Token süresi doldu"}
        except pyjwt_module.InvalidTokenError as e:
            return {"valid": False, "error": f"Geçersiz token: {str(e)}"}
    else:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return {"valid": False, "error": "Geçersiz JWT formatı"}

            header_b64, payload_b64, sig_b64 = parts
            signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

            # Imza Kontrolü
            expected_sig = hmac.new(secret_key.encode('utf-8'), signing_input, hashlib.sha256).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

            if not hmac.compare_digest(sig_b64, expected_sig_b64):
                return {"valid": False, "error": "Geçersiz JWT İmzası"}

            # Payload Decode & Süre Kontrolü
            padding = "=" * (-len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
            payload = json.loads(payload_json)

            now = int(time.time())
            if payload.get("exp") and now > payload["exp"]:
                return {"valid": False, "error": "Token süresi doldu"}

            return {"valid": True, "payload": payload}
        except Exception as e:
            return {"valid": False, "error": f"Token doğrulama hatası: {str(e)}"}


class AuthService:
    """
    Rate limiting ve Brute-Force anti-spoofing güvenlik servisi.
    """
    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 60):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self.attempts = {}  # {user_id: [timestamp1, timestamp2, ...]}

    def check_rate_limit(self, user_id: str) -> dict:
        now = time.time()
        user_attempts = self.attempts.get(user_id, [])

        valid_attempts = [t for t in user_attempts if now - t < self.lockout_seconds]
        self.attempts[user_id] = valid_attempts

        if len(valid_attempts) >= self.max_attempts:
            remaining_lockout = int(self.lockout_seconds - (now - valid_attempts[0]))
            return {
                "allowed": False,
                "reason": f"Çok fazla başarısız deneme. Lütfen {remaining_lockout} saniye bekleyin.",
                "remaining_seconds": remaining_lockout
            }

        return {"allowed": True, "attempts_count": len(valid_attempts)}

    def record_failed_attempt(self, user_id: str):
        now = time.time()
        if user_id not in self.attempts:
            self.attempts[user_id] = []
        self.attempts[user_id].append(now)

    def reset_attempts(self, user_id: str):
        if user_id in self.attempts:
            del self.attempts[user_id]
