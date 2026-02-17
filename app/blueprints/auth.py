from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.db import get_db

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        user = db.execute(
            'SELECT id, username, password_hash, display_name, role, is_active FROM user WHERE username = ?',
            (username,)
        ).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('Vaš račun je deaktiviran.', 'danger')
            else:
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                session['user_display_name'] = user['display_name']
                session.permanent = True
                flash('Uspješna prijava.', 'success')
                next_url = request.args.get('next') or url_for('main.index')
                return redirect(next_url)
        else:
            flash('Neispravno korisničko ime ili lozinka.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    session.pop('user_display_name', None)
    flash('Uspješna odjava.', 'success')
    return redirect(url_for('main.index'))
