import numpy as np
from core.liveness_detector import verify_liveness, detect_texture_spoofing
from core.face_recognizer import extract_face_embedding, compare_faces
from security.auth_service import (
    generate_key_from_passphrase,
    encrypt_biometric_data,
    decrypt_biometric_data,
    generate_secure_jwt,
    AuthService
)

class BiometricAuthEngine:
    """
    Forensic Vision - Biyometrik Güvenlik & Anti-Spoofing Orkestratör Engine.
    """

    def __init__(self, jwt_secret: str = "forensic_jwt_super_secret_key_2026"):
        self.jwt_secret = jwt_secret
        self.auth_service = AuthService(max_attempts=5, lockout_seconds=60)

    def register_user(self, user_id: str, face_image: np.ndarray, passphrase: str) -> dict:
        """
        Yeni bir kullanıcının yüz biyometrik verisini çıkarır ve AES-256 ile şifreleyerek kayıt verisi oluşturur.

        :param user_id: Kullanıcı benzersiz kimliği.
        :param face_image: Kullanıcının kayıt aşamasındaki yüz görseli.
        :param passphrase: Biyometrik veriyi şifrelemek için kullanılacak gizli anahtar/parola.
        :return: Kayıt veri sözlüğü.
        """
        if face_image is None or face_image.size == 0:
            return {"status": "error", "message": "Geçersiz görsel!"}

        # 1. Yüz vektörünü çıkar
        embedding = extract_face_embedding(face_image)

        # 2. Fernet AES-256 anahtarı türet ve şifrele
        secret_key = generate_key_from_passphrase(passphrase)
        encrypted_embedding_str = encrypt_biometric_data(embedding, secret_key)

        return {
            "status": "success",
            "user_id": user_id,
            "encrypted_biometric_data": encrypted_embedding_str,
            "vector_dimension": len(embedding)
        }

    def authenticate_user(
        self,
        user_id: str,
        input_media: list[np.ndarray] | np.ndarray,
        encrypted_biometric_data: str,
        passphrase: str,
        similarity_threshold: float = 0.65
    ) -> dict:
        """
        Kullanıcının canlılığını doğrular, biyometrik yüzünü eşleştirir ve JWT yetkilendirme token'ı üretir.

        :param user_id: Kullanıcı kimliği.
        :param input_media: Tek görsel veya video kareleri dizisi.
        :param encrypted_biometric_data: Kayıtlı AES-256 şifreli biyometrik veri.
        :param passphrase: Şifre çözme parolası.
        :param similarity_threshold: Yüz benzerlik eşiği.
        :return: Kimlik doğrulama sonucu.
        """
        # 1. Rate limiting kontrolü
        rate_check = self.auth_service.check_rate_limit(user_id)
        if not rate_check["allowed"]:
            return {
                "status": "denied",
                "reason": rate_check["reason"],
                "lockout_remaining": rate_check["remaining_seconds"]
            }

        frames = input_media if isinstance(input_media, list) else [input_media]

        # 2. Anti-Spoofing & Canlılık Testi
        liveness_res = verify_liveness(frames)
        if not liveness_res["is_live"]:
            self.auth_service.record_failed_attempt(user_id)
            return {
                "status": "failed",
                "reason": "Anti-Spoofing İhlali / Canlılık Doğrulaması Başarısız!",
                "liveness_confidence": liveness_res["liveness_confidence"],
                "details": liveness_res["details"]
            }

        # 3. Şifreli biyometrik veriyi çöz
        try:
            secret_key = generate_key_from_passphrase(passphrase)
            registered_embedding = decrypt_biometric_data(encrypted_biometric_data, secret_key)
        except Exception as e:
            self.auth_service.record_failed_attempt(user_id)
            return {
                "status": "failed",
                "reason": f"Biyometrik veri şifre çözme hatası (Yanlış Parola): {str(e)}"
            }

        # 4. Giriş yapılan kareden yüz vektörünü çıkar ve eşleştir
        input_embedding = extract_face_embedding(frames[0])
        matching_res = compare_faces(input_embedding, registered_embedding, threshold=similarity_threshold)

        if not matching_res["is_match"]:
            self.auth_service.record_failed_attempt(user_id)
            return {
                "status": "failed",
                "reason": "Yüz Biyometrik Eşleşmesi Başarısız! (Kişi Doğrulanamadı)",
                "similarity_score": matching_res["similarity_score"],
                "threshold": similarity_threshold
            }

        # 5. Başarılı Yetkilendirme: Rate limit sıfırla & JWT Token Üret
        self.auth_service.reset_attempts(user_id)
        jwt_token = generate_secure_jwt(user_id, self.jwt_secret, expires_in_seconds=3600)

        return {
            "status": "authenticated",
            "user_id": user_id,
            "jwt_token": jwt_token,
            "liveness_verified": True,
            "liveness_confidence": liveness_res["liveness_confidence"],
            "similarity_score": matching_res["similarity_score"],
            "message": "Biyometrik Kimlik Doğrulama Başarılı!"
        }

if __name__ == "__main__":
    print("BiometricAuthEngine modülü hazır. Test için test_biometric.py betiğini çalıştırın.")
