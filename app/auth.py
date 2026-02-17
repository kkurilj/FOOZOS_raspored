from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify


def is_admin():
    """Provjeri je li trenutni korisnik prijavljen kao admin."""
    return session.get('is_admin', False)


def login_required(f):
    """Decorator koji preusmjerava na login stranicu ako korisnik nije prijavljen."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Morate se prijaviti za pristup ovoj stranici.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def api_login_required(f):
    """Decorator za API rute - vraca JSON 403 umjesto redirecta."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return jsonify({'error': 'Nemate dozvolu za ovu radnju.'}), 403
        return f(*args, **kwargs)
    return decorated_function
