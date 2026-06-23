import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import current_app, jsonify, request, session

from .db import get_db


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def rotate_session(user_id: int | None = None) -> str:
    session.clear()
    session.permanent = True
    if user_id is not None:
        session["user_id"] = user_id
    return ensure_csrf_token()


def csrf_protect() -> None:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    expected = session.get("csrf_token")
    supplied = request.headers.get("X-CSRF-Token", "")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        return jsonify({"error": "csrf_invalid", "message": "Session expirée ou jeton de sécurité invalide. Rechargez la page."}), 403
    return None


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute(
        "SELECT id, email, name, role, age_group, created_at, consent_version FROM users WHERE id = ? AND deleted_at IS NULL",
        (user_id,),
    ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "authentication_required", "message": "Connexion requise."}), 401
        return view(*args, **kwargs)

    return wrapped


def client_ip() -> str:
    return (request.remote_addr or "unknown").strip()


def rate_limit_key(value: str) -> str:
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()


def consume_rate_limit(action: str, raw_key: str, limit: int, window_seconds: int) -> bool:
    """Retourne True si l'action est autorisée, False si la limite est atteinte."""
    db = get_db()
    key = rate_limit_key(raw_key)
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).isoformat(timespec="seconds")
    db.execute("DELETE FROM rate_limit_events WHERE action = ? AND created_at < ?", (action, cutoff))
    count = db.execute(
        "SELECT COUNT(*) FROM rate_limit_events WHERE action = ? AND event_key = ? AND created_at >= ?",
        (action, key, cutoff),
    ).fetchone()[0]
    if count >= limit:
        db.commit()
        return False
    db.execute(
        "INSERT INTO rate_limit_events(event_key, action, created_at) VALUES (?, ?, ?)",
        (key, action, utc_now()),
    )
    db.commit()
    return True


def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
        "script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; "
        "connect-src 'self'; frame-src https://app.heygen.com; form-action 'self'",
    )
    if current_app.config.get("SESSION_COOKIE_SECURE"):
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.path.startswith("/api/") or request.path.startswith("/certificate"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response
