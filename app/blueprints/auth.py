from collections import defaultdict
from time import time

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.db import get_db

bp = Blueprint('auth', __name__)

# Rate limiting: max 5 pokušaja u 5 minuta po IP adresi
_login_attempts = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW = 300  # sekundi


def _is_rate_limited(ip):
    now = time()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < _WINDOW]
    return len(_login_attempts[ip]) >= _MAX_ATTEMPTS


def _record_attempt(ip):
    _login_attempts[ip].append(time())


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        ip = request.remote_addr or '0.0.0.0'

        if _is_rate_limited(ip):
            flash('Previše neuspješnih pokušaja prijave. Pokušajte ponovno za nekoliko minuta.', 'danger')
            return render_template('auth/login.html')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute(
            'SELECT id, username, password_hash, first_name, last_name, role, is_active FROM user WHERE username = ?',
            (username,)
        ).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('Vaš račun je deaktiviran.', 'danger')
            else:
                # Uspješna prijava - resetiraj pokušaje
                _login_attempts.pop(ip, None)
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                session['user_display_name'] = f"{user['first_name']} {user['last_name']}".strip()
                session.permanent = True
                flash('Uspješna prijava.', 'success')
                next_url = request.args.get('next') or url_for('main.index')
                return redirect(next_url)
        else:
            _record_attempt(ip)
            remaining = _MAX_ATTEMPTS - len(_login_attempts[ip])
            if remaining > 0:
                flash(f'Neispravno korisničko ime ili lozinka. Preostalo pokušaja: {remaining}.', 'danger')
            else:
                flash('Previše neuspješnih pokušaja prijave. Pokušajte ponovno za nekoliko minuta.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    session.pop('user_display_name', None)
    flash('Uspješna odjava.', 'success')
    return redirect(url_for('main.index'))
