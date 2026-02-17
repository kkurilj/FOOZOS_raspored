from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify


def is_admin():
    """Provjeri je li trenutni korisnik prijavljen (bilo koja uloga)."""
    return 'user_id' in session


def is_super_admin():
    """Provjeri je li trenutni korisnik super admin."""
    return session.get('user_role') == 'super_admin'


def get_current_user_id():
    """Vrati ID trenutnog korisnika ili None."""
    return session.get('user_id')


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


def super_admin_required(f):
    """Decorator koji dopušta pristup samo super adminima."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            flash('Morate se prijaviti za pristup ovoj stranici.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not is_super_admin():
            flash('Nemate dozvolu za pristup ovoj stranici.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
