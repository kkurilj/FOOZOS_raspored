from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db
from app.auth import login_required, super_admin_required, get_current_user_id
from app.audit import log_audit

bp = Blueprint('user', __name__)

ROLES = [('super_admin', 'Super Admin'), ('admin', 'Admin')]
MIN_PASSWORD_LENGTH = 10


def _display_name(first_name, last_name):
    """Generiraj ime za prikaz iz imena i prezimena."""
    return f'{first_name} {last_name}'.strip()


@bp.route('/')
@super_admin_required
def index():
    db = get_db()
    users = db.execute('SELECT * FROM user ORDER BY id').fetchall()
    return render_template('user/index.html', users=users)


@bp.route('/create', methods=['GET', 'POST'])
@super_admin_required
def create():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        role = request.form.get('role', 'admin')

        if not username or not first_name or not last_name:
            flash('Korisničko ime, ime i prezime su obavezni.', 'danger')
        elif not password:
            flash('Lozinka je obavezna.', 'danger')
        elif len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Lozinka mora imati najmanje {MIN_PASSWORD_LENGTH} znakova.', 'danger')
        elif password != password_confirm:
            flash('Lozinke se ne podudaraju.', 'danger')
        elif role not in ('super_admin', 'admin'):
            flash('Neispravna uloga.', 'danger')
        else:
            db = get_db()
            existing = db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone()
            if existing:
                flash('Korisničko ime je već zauzeto.', 'danger')
            else:
                cursor = db.execute(
                    'INSERT INTO user (username, password_hash, first_name, last_name, role) VALUES (?, ?, ?, ?, ?)',
                    (username, generate_password_hash(password), first_name, last_name, role)
                )
                log_audit('create', 'user', f'Dodan korisnik "{first_name} {last_name}" ({username}, {role})', cursor.lastrowid, db)
                db.commit()
                flash(f'Korisnik "{first_name} {last_name}" je dodan.', 'success')
                return redirect(url_for('user.index'))

    return render_template('user/form.html', roles=ROLES)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@super_admin_required
def edit(id):
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (id,)).fetchone()
    if user is None:
        flash('Korisnik nije pronađen.', 'danger')
        return redirect(url_for('user.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'admin')
        is_active = 1 if request.form.get('is_active') else 0
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()

        if not first_name or not last_name:
            flash('Ime i prezime su obavezni.', 'danger')
        elif password and len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Lozinka mora imati najmanje {MIN_PASSWORD_LENGTH} znakova.', 'danger')
        elif password and password != password_confirm:
            flash('Lozinke se ne podudaraju.', 'danger')
        elif role not in ('super_admin', 'admin'):
            flash('Neispravna uloga.', 'danger')
        else:
            display_name = _display_name(first_name, last_name)
            if password:
                db.execute(
                    'UPDATE user SET first_name = ?, last_name = ?, role = ?, is_active = ?, password_hash = ? WHERE id = ?',
                    (first_name, last_name, role, is_active, generate_password_hash(password), id)
                )
            else:
                db.execute(
                    'UPDATE user SET first_name = ?, last_name = ?, role = ?, is_active = ? WHERE id = ?',
                    (first_name, last_name, role, is_active, id)
                )
            log_audit('update', 'user', f'Ažuriran korisnik "{display_name}" ({user["username"]})', id, db)
            db.commit()
            if id == get_current_user_id():
                session['user_role'] = role
                session['user_display_name'] = display_name
            flash('Korisnik je ažuriran.', 'success')
            return redirect(url_for('user.index'))

    return render_template('user/form.html', user=user, roles=ROLES)


@bp.route('/<int:id>/delete', methods=['POST'])
@super_admin_required
def delete(id):
    if id == get_current_user_id():
        flash('Ne možete obrisati vlastiti račun.', 'danger')
        return redirect(url_for('user.index'))

    db = get_db()
    u = db.execute('SELECT username, first_name, last_name FROM user WHERE id = ?', (id,)).fetchone()
    if u:
        log_audit('delete', 'user', f'Obrisan korisnik "{u["first_name"]} {u["last_name"]}" ({u["username"]})', id, db)
    db.execute('DELETE FROM user WHERE id = ?', (id,))
    db.commit()
    flash('Korisnik je obrisan.', 'success')
    return redirect(url_for('user.index'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (get_current_user_id(),)).fetchone()

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        new_password_confirm = request.form.get('new_password_confirm', '')

        if not first_name or not last_name:
            flash('Ime i prezime su obavezni.', 'danger')
            return render_template('user/profile.html', user=user)

        if new_password:
            if len(new_password) < MIN_PASSWORD_LENGTH:
                flash(f'Lozinka mora imati najmanje {MIN_PASSWORD_LENGTH} znakova.', 'danger')
                return render_template('user/profile.html', user=user)
            if not check_password_hash(user['password_hash'], current_password):
                flash('Trenutna lozinka je neispravna.', 'danger')
                return render_template('user/profile.html', user=user)
            if new_password != new_password_confirm:
                flash('Nove lozinke se ne podudaraju.', 'danger')
                return render_template('user/profile.html', user=user)
            db.execute(
                'UPDATE user SET first_name = ?, last_name = ?, password_hash = ? WHERE id = ?',
                (first_name, last_name, generate_password_hash(new_password), user['id'])
            )
        else:
            db.execute(
                'UPDATE user SET first_name = ?, last_name = ? WHERE id = ?',
                (first_name, last_name, user['id'])
            )
        db.commit()
        session['user_display_name'] = _display_name(first_name, last_name)
        flash('Profil je ažuriran.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html', user=user)
