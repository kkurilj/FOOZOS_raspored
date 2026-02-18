from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.auth import login_required, super_admin_required
from app.audit import log_audit

bp = Blueprint('academic_year', __name__)


@bp.route('/')
@login_required
def index():
    db = get_db()
    years = db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall()
    return render_template('academic_year/index.html', years=years)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Naziv akademske godine je obavezan.', 'danger')
        else:
            db = get_db()
            try:
                cursor = db.execute('INSERT INTO academic_year (name) VALUES (?)', (name,))
                log_audit('create', 'academic_year', f'Dodana akademska godina "{name}"', cursor.lastrowid, db)
                db.commit()
                flash(f'Akademska godina "{name}" je dodana.', 'success')
                return redirect(url_for('academic_year.index'))
            except db.IntegrityError:
                flash(f'Akademska godina "{name}" već postoji.', 'danger')
    return render_template('academic_year/form.html')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    year = db.execute('SELECT * FROM academic_year WHERE id = ?', (id,)).fetchone()
    if year is None:
        flash('Akademska godina nije pronađena.', 'danger')
        return redirect(url_for('academic_year.index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Naziv akademske godine je obavezan.', 'danger')
        else:
            try:
                db.execute('UPDATE academic_year SET name = ? WHERE id = ?', (name, id))
                log_audit('update', 'academic_year', f'Ažurirana akademska godina "{year["name"]}" → "{name}"', id, db)
                db.commit()
                flash(f'Akademska godina je ažurirana.', 'success')
                return redirect(url_for('academic_year.index'))
            except db.IntegrityError:
                flash(f'Akademska godina "{name}" već postoji.', 'danger')
    return render_template('academic_year/form.html', year=year)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    year = db.execute('SELECT name FROM academic_year WHERE id = ?', (id,)).fetchone()
    log_audit('delete', 'academic_year', f'Obrisana akademska godina "{year["name"]}"' if year else f'Obrisana akademska godina ID={id}', id, db)
    db.execute('DELETE FROM academic_year WHERE id = ?', (id,))
    db.commit()
    flash('Akademska godina je obrisana.', 'success')
    return redirect(url_for('academic_year.index'))


@bp.route('/<int:id>/set-default', methods=['POST'])
@super_admin_required
def set_default(id):
    db = get_db()
    year = db.execute('SELECT * FROM academic_year WHERE id = ?', (id,)).fetchone()
    if year is None:
        flash('Akademska godina nije pronađena.', 'danger')
        return redirect(url_for('academic_year.index'))
    db.execute('UPDATE academic_year SET is_default = 0')
    db.execute('UPDATE academic_year SET is_default = 1 WHERE id = ?', (id,))
    log_audit('update', 'academic_year', f'Postavljena zadana akademska godina "{year["name"]}"', id, db)
    db.commit()
    flash(f'Akademska godina "{year["name"]}" je postavljena kao zadana.', 'success')
    return redirect(url_for('academic_year.index'))
