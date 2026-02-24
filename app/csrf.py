import hmac
import secrets
from flask import session, request, abort
from markupsafe import Markup


def generate_csrf_token():
    """Generiraj CSRF token i spremi u session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def csrf_input():
    """Vrati hidden input HTML za CSRF token."""
    token = generate_csrf_token()
    return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')


def validate_csrf():
    """Validiraj CSRF token na POST/PUT/DELETE/PATCH zahtjevima."""
    if request.method not in ('POST', 'PUT', 'DELETE', 'PATCH'):
        return

    # Token može doći iz forme ili X-CSRFToken headera (AJAX)
    token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    session_token = session.get('_csrf_token', '')
    if not token or not hmac.compare_digest(token, session_token):
        abort(403)
