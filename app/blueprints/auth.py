from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('is_admin'):
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if (username == current_app.config['ADMIN_USERNAME'] and
                check_password_hash(current_app.config['ADMIN_PASSWORD_HASH'], password)):
            session['is_admin'] = True
            session.permanent = True
            flash('Uspješna prijava.', 'success')
            next_url = request.args.get('next') or url_for('main.index')
            return redirect(next_url)
        else:
            flash('Neispravno korisničko ime ili lozinka.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('Uspješna odjava.', 'success')
    return redirect(url_for('main.index'))
