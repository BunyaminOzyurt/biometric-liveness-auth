# 🛡️ Biometric Security & Anti-Spoofing Authentication System

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8.svg)
![Cryptography](https://img.shields.io/badge/AES--256-Fernet-green.svg)
![JWT](https://img.shields.io/badge/JWT-RFC7519-orange.svg)
![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)

**Biometric Security & Anti-Spoofing Authentication System** is an enterprise-grade biometric authorization library. It combines 128-dimensional facial embedding recognition with multi-layered liveness verification (blink detection, 3D head pose, and FFT/Laplacian texture anti-spoofing) to prevent photo, screen replay, and deepfake presentation attacks.

---

## 🚀 Key Features

### 👁️ 1. Liveness Detection & Anti-Spoofing
* **Eye Aspect Ratio (EAR) Blink Detection:** Tracks eye landmarks to confirm active human presence.
* **3D Head Pose & Asymmetry Tracking:** Evaluates Yaw/Pitch/Roll micro-movements across video frames.
* **Texture & Moire Pattern Anti-Spoofing:** Analyzes Laplacian variance (focus/blur) and 2D FFT high-frequency noise to block digital screens, printed photos, and video replay attacks.

### 👤 2. Biometric Face Recognition
* **128-D Feature Embedding:** Extracts normalized L2 feature vectors from aligned facial regions.
* **Cosine Similarity & Euclidean Distance Matching:** Compares live embeddings against registered biometric templates with configurable matching thresholds (`threshold = 0.65`).

### 🔐 3. Cryptographic Storage & Security
* **AES-256 Biometric Encryption:** Biometric feature vectors are never stored in plaintext. They are encrypted using Fernet (AES-256-CBC + HMAC-SHA256) with PBKDF2 key derivation.
* **RFC 7519 JWT Authentication:** Generates cryptographically signed JWT authorization tokens upon successful liveness + identity verification.
* **Brute-Force & Rate Limiting:** Enforces automatic lockout periods after repeated failed authentication attempts.

---

## 🛠️ Project Architecture

```
[ Camera / Input Frame Stream ]
             │
             ├──► 1. Liveness Detector ──► EAR Blink Check, Head Pose, Texture Moire Analysis
             │
             ├──► 2. Face Embedder     ──► 128-D Vector Extraction & Cosine Similarity
             │
             └──► 3. Security Engine   ──► AES-256 Decryption, Rate Limiting & JWT Issuer
             │
             ▼
[ Authenticated JWT Token / Access Denied ]
```

---

## 📂 File Structure

```text
biometric_liveness_auth/
│
├── core/
│   ├── __init__.py
│   ├── liveness_detector.py   # EAR, Head Pose & Moire Texture Anti-Spoofing
│   └── face_recognizer.py     # 128-D Face Embeddings & Cosine Matching
│
├── security/
│   ├── __init__.py
│   └── auth_service.py        # AES-256 Encryption, Rate Limiting & JWT Auth
│
├── biometric_engine.py        # Main BiometricAuthEngine Orchestrator
├── test_biometric.py          # Automated End-to-End Test Suite
├── requirements.txt           # Dependency requirements
└── README.md                  # Documentation
```

---

## ⚡ Quick Start & Usage

### 1. User Registration
```python
from biometric_engine import BiometricAuthEngine
import cv2

engine = BiometricAuthEngine(jwt_secret="your_jwt_secret_key")
face_image = cv2.imread("user_face.jpg")

# Register user and encrypt 128-D biometric vector with user passphrase
registration = engine.register_user(
    user_id="user_123",
    face_image=face_image,
    passphrase="UserSecretPassphrase!"
)

encrypted_biometric_data = registration["encrypted_biometric_data"]
```

### 2. User Authentication (Liveness + Identity)
```python
# Authenticate live video frames
live_frames = [cv2.imread("frame1.jpg"), cv2.imread("frame2.jpg")]

auth_result = engine.authenticate_user(
    user_id="user_123",
    input_media=live_frames,
    encrypted_biometric_data=encrypted_biometric_data,
    passphrase="UserSecretPassphrase!"
)

if auth_result["status"] == "authenticated":
    print("✅ Authenticated! JWT Token:", auth_result["jwt_token"])
else:
    print("❌ Failed:", auth_result["reason"])
```

---

## 🧪 Running Automated Tests

Run the test suite to verify liveness detection, AES-256 encryption, and anti-spoofing defense:

```bash
cd /Users/bunyaminozyurt/Desktop/biometric_liveness_auth
python3 test_biometric.py
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
