from ipaddress import ip_address, ip_network
from time import time

from urllib.parse import urlparse, urljoin

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from app.db import get_db
from app.auth import login_required
from app.audit import log_audit

bp = Blueprint('auth', __name__)


def _is_safe_url(target):
    """Provjeri da je URL interni (zaštita od open redirect)."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


# Rate limiting
_MAX_ATTEMPTS = 3
_TRUSTED_MAX_ATTEMPTS = 20
_TRUSTED_NETWORK = ip_network('193.198.137.0/27')
_LOCKOUT = 900  # 15 minuta


def _max_attempts_for_ip(ip):
    """Vrati dopušteni broj pokušaja ovisno o IP adresi."""
    try:
        if ip_address(ip) in _TRUSTED_NETWORK:
            return _TRUSTED_MAX_ATTEMPTS
    except ValueError:
        pass
    return _MAX_ATTEMPTS


def _get_client_ip():
    """Vrati IP adresu klijenta (podržava reverse proxy preko ProxyFix)."""
    return request.remote_addr or '0.0.0.0'


def _cleanup_old_attempts(db):
    """Obriši pokušaje starije od LOCKOUT perioda."""
    db.execute('DELETE FROM login_attempt WHERE attempted_at < ?', (time() - _LOCKOUT,))


def _is_rate_limited(db, ip):
    _cleanup_old_attempts(db)
    count = db.execute(
        'SELECT COUNT(*) FROM login_attempt WHERE ip_address = ? AND attempted_at >= ?',
        (ip, time() - _LOCKOUT)
    ).fetchone()[0]
    return count >= _max_attempts_for_ip(ip)


def _lockout_remaining(db, ip):
    """Vrati preostalo vrijeme blokade u minutama."""
    row = db.execute(
        'SELECT MIN(attempted_at) FROM login_attempt WHERE ip_address = ? AND attempted_at >= ?',
        (ip, time() - _LOCKOUT)
    ).fetchone()
    if not row or not row[0]:
        return 0
    remaining = _LOCKOUT - (time() - row[0])
    return max(1, int(remaining / 60 + 0.5))


def _record_attempt(db, ip):
    db.execute('INSERT INTO login_attempt (ip_address, attempted_at) VALUES (?, ?)', (ip, time()))
    db.commit()


def _clear_attempts(db, ip):
    db.execute('DELETE FROM login_attempt WHERE ip_address = ?', (ip,))
    db.commit()


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        db = get_db()
        ip = _get_client_ip()

        if _is_rate_limited(db, ip):
            mins = _lockout_remaining(db, ip)
            flash(f'Previše neuspješnih pokušaja prijave. Pokušajte ponovno za {mins} min.', 'danger')
            return render_template('auth/login.html')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = db.execute(
            'SELECT id, username, password_hash, first_name, last_name, role, is_active, must_change_password FROM user WHERE username = ?',
            (username,)
        ).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                log_audit('login_failed', 'auth', f'Pokušaj prijave na deaktivirani račun "{username}" (IP: {ip})',
                          db=db, user_id=user['id'], user_name=username)
                db.commit()
                flash('Vaš račun je deaktiviran.', 'danger')
            else:
                # Uspješna prijava - resetiraj pokušaje
                _clear_attempts(db, ip)

                # Zaštita od session fixation - regeneriraj session
                session.clear()
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                display = f"{user['first_name']} {user['last_name']}".strip()
                session['user_display_name'] = display
                session.permanent = True

                log_audit('login', 'auth', f'Uspješna prijava korisnika "{display}" (IP: {ip})',
                          db=db, user_id=user['id'], user_name=display)
                db.commit()

                if user['must_change_password']:
                    flash('Morate promijeniti lozinku prije nastavka rada.', 'warning')
                    return redirect(url_for('auth.force_change_password'))

                flash('Uspješna prijava.', 'success')
                next_url = request.args.get('next', '')
                if not next_url or not _is_safe_url(next_url):
                    next_url = url_for('main.index')
                return redirect(next_url)
        else:
            _record_attempt(db, ip)
            log_audit('login_failed', 'auth', f'Neuspjela prijava za korisnika "{username}" (IP: {ip})',
                      db=db, user_name=username)
            db.commit()
            if _is_rate_limited(db, ip):
                mins = _lockout_remaining(db, ip)
                flash(f'Previše neuspješnih pokušaja prijave. Pokušajte ponovno za {mins} min.', 'danger')
            else:
                flash('Neispravno korisničko ime ili lozinka.', 'danger')

    return render_template('auth/login.html')


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def force_change_password():
    """Stranica za obaveznu promjenu lozinke."""
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    if not user or not user['must_change_password']:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        new_password_confirm = request.form.get('new_password_confirm', '')

        if len(new_password) < 10:
            flash('Lozinka mora imati najmanje 10 znakova.', 'danger')
        elif new_password != new_password_confirm:
            flash('Lozinke se ne podudaraju.', 'danger')
        elif check_password_hash(user['password_hash'], new_password):
            flash('Nova lozinka mora biti različita od trenutne.', 'danger')
        else:
            db.execute(
                'UPDATE user SET password_hash = ?, must_change_password = 0 WHERE id = ?',
                (generate_password_hash(new_password), user['id'])
            )
            db.commit()
            flash('Lozinka je uspješno promijenjena.', 'success')
            return redirect(url_for('main.index'))

    return render_template('auth/change_password.html')


@bp.route('/logout', methods=['POST'])
def logout():
    display = session.get('user_display_name', 'Nepoznat')
    uid = session.get('user_id')
    if uid:
        log_audit('logout', 'auth', f'Odjava korisnika "{display}"',
                  user_id=uid, user_name=display)
        get_db().commit()
    session.clear()
    flash('Uspješna odjava.', 'success')
    return redirect(url_for('main.index'))
