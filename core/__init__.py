"""
Biometric Core - Liveness Detection & Face Recognition Module
"""

from .liveness_detector import calculate_ear, detect_texture_spoofing, verify_liveness
from .face_recognizer import extract_face_embedding, compare_faces

__all__ = [
    "calculate_ear",
    "detect_texture_spoofing",
    "verify_liveness",
    "extract_face_embedding",
    "compare_faces",
]
