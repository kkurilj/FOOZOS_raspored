import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _get_secret_key():
    """Dohvati SECRET_KEY iz env varijable ili generiraj i spremi u datoteku."""
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    key_file = os.path.join(BASE_DIR, 'instance', '.secret_key')
    try:
        with open(key_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        key = secrets.token_hex(32)
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(key)
        return key


class Config:
    SECRET_KEY = _get_secret_key()
    DATABASE = os.path.join(BASE_DIR, 'instance', 'raspored.db')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') != 'development'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minuta neaktivnosti
    PREFERRED_URL_SCHEME = 'https'
