from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db
from app.auth import login_required, super_admin_required, get_current_user_id

bp = Blueprint('user', __name__)

ROLES = [('super_admin', 'Super Admin'), ('admin', 'Admin')]


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
        display_name = request.form.get('display_name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'admin')

        if not username or not password:
            flash('Korisničko ime i lozinka su obavezni.', 'danger')
        elif role not in ('super_admin', 'admin'):
            flash('Neispravna uloga.', 'danger')
        else:
            db = get_db()
            existing = db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone()
            if existing:
                flash('Korisničko ime je već zauzeto.', 'danger')
            else:
                db.execute(
                    'INSERT INTO user (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)',
                    (username, generate_password_hash(password), display_name, role)
                )
                db.commit()
                flash(f'Korisnik "{username}" je dodan.', 'success')
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
        display_name = request.form.get('display_name', '').strip()
        role = request.form.get('role', 'admin')
        is_active = 1 if request.form.get('is_active') else 0
        password = request.form.get('password', '').strip()

        if role not in ('super_admin', 'admin'):
            flash('Neispravna uloga.', 'danger')
        else:
            if password:
                db.execute(
                    'UPDATE user SET display_name = ?, role = ?, is_active = ?, password_hash = ? WHERE id = ?',
                    (display_name, role, is_active, generate_password_hash(password), id)
                )
            else:
                db.execute(
                    'UPDATE user SET display_name = ?, role = ?, is_active = ? WHERE id = ?',
                    (display_name, role, is_active, id)
                )
            db.commit()
            # Ažuriraj session ako je korisnik sam sebe uredio
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
        display_name = request.form.get('display_name', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        if new_password:
            if not check_password_hash(user['password_hash'], current_password):
                flash('Trenutna lozinka je neispravna.', 'danger')
                return render_template('user/profile.html', user=user)
            db.execute(
                'UPDATE user SET display_name = ?, password_hash = ? WHERE id = ?',
                (display_name, generate_password_hash(new_password), user['id'])
            )
        else:
            db.execute(
                'UPDATE user SET display_name = ? WHERE id = ?',
                (display_name, user['id'])
            )
        db.commit()
        session['user_display_name'] = display_name
        flash('Profil je ažuriran.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html', user=user)
