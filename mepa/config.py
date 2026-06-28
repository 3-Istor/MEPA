import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-before-deploy")
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "data" / "mepa.sqlite"))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
    GEMINI_RETRY_ATTEMPTS = max(1, min(5, int(os.getenv("GEMINI_RETRY_ATTEMPTS", "3"))))
    PROMPT_ATTEMPT_LIMIT = int(os.getenv("PROMPT_ATTEMPT_LIMIT", "3"))
    LOCAL_VIDEO_PATH = os.getenv("LOCAL_VIDEO_PATH", str(PROJECT_ROOT / "video-introduction-ia.mp4"))
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    JSON_AS_ASCII = False
    TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() == "true"
