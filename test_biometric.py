import json
import numpy as np
import cv2
from biometric_engine import BiometricAuthEngine
from security.auth_service import verify_jwt_token

def generate_synthetic_face(has_noise: bool = False, is_blurred: bool = False) -> np.ndarray:
    """
    Test amaçlı sentetik yüz görseli ve canlılık karesi üretir.
    """
    h, w = 200, 200
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # Cilt tonu arka plan
    img[:, :] = (180, 190, 230)

    # Yüz ovali
    cv2.ellipse(img, (100, 100), (60, 80), 0, 0, 360, (140, 150, 210), -1)

    # Gözler
    cv2.circle(img, (75, 80), 10, (255, 255, 255), -1)
    cv2.circle(img, (125, 80), 10, (255, 255, 255), -1)
    cv2.circle(img, (75, 80), 4, (0, 0, 0), -1)
    cv2.circle(img, (125, 80), 4, (0, 0, 0), -1)

    # Ağız
    cv2.ellipse(img, (100, 140), (25, 10), 0, 0, 180, (50, 50, 180), 3)

    if has_noise:
        # Ekran Moire gürültüsü ekle
        noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)

    if is_blurred:
        # Fotoğraf ekran baskı bulanıklığı
        img = cv2.GaussianBlur(img, (15, 15), 0)

    return img

def run_tests():
    print("=" * 60)
    print("🚀 BiometricAuthEngine & Anti-Spoofing Otomatik Test...")
    print("=" * 60)

    engine = BiometricAuthEngine(jwt_secret="test_secret_key_2026")
    user_id = "user_bunyamin_01"
    passphrase = "SecureUserPassphrase123!"

    # 1. Kullanıcı Kayıt Testi
    face_img = generate_synthetic_face()
    reg_result = engine.register_user(user_id, face_img, passphrase)

    print("\n📝 Kayıt Sonucu:")
    print(json.dumps(reg_result, indent=2, ensure_ascii=False))

    assert reg_result["status"] == "success", "Kayıt Başarısız!"
    encrypted_data = reg_result["encrypted_biometric_data"]

    # 2. Başarılı Canlılık + Biyometrik Doğrulama Testi
    live_frames = [generate_synthetic_face() for _ in range(3)]
    auth_result = engine.authenticate_user(user_id, live_frames, encrypted_data, passphrase)

    print("\n🔑 Başarılı Kimlik Doğrulama Sonucu:")
    print(json.dumps(auth_result, indent=2, ensure_ascii=False))

    assert auth_result["status"] == "authenticated", "Doğrulama Başarısız!"
    assert auth_result["liveness_verified"] is True, "Canlılık Doğrulanamadı!"
    assert "jwt_token" in auth_result, "JWT Token Üretilemedi!"

    # 3. JWT Token Doğrulama Testi
    token_check = verify_jwt_token(auth_result["jwt_token"], "test_secret_key_2026")
    print("\n🛡️ JWT Token Doğrulama:")
    print(token_check)
    assert token_check["valid"] is True, "JWT Token Geçersiz!"

    # 4. Anti-Spoofing (Fotoğraf/Ekran Saldırısı) Engelleme Testi
    spoof_frames = [generate_synthetic_face(has_noise=True, is_blurred=True) for _ in range(3)]
    spoof_result = engine.authenticate_user("user_attacker", spoof_frames, encrypted_data, passphrase)

    print("\n🚫 Anti-Spoofing Engelleme Testi Sonucu:")
    print(json.dumps(spoof_result, indent=2, ensure_ascii=False))

    assert spoof_result["status"] == "failed", "Anti-Spoofing Saldırısı Engellenemedi!"

    print("\n" + "=" * 60)
    print("🎉 TÜM BİYOMETRİK VE ANTI-SPOOFING TESTLERİ BAŞARIYLA GEÇTİ!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
