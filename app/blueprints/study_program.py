from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db

bp = Blueprint('study_program', __name__)


@bp.route('/')
def index():
    db = get_db()
    programs = db.execute('SELECT * FROM study_program ORDER BY name').fetchall()
    return render_template('study_program/index.html', programs=programs)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name'].strip()
        code = request.form['code'].strip()
        if not name or not code:
            flash('Sva polja su obavezna.', 'danger')
        else:
            db = get_db()
            try:
                db.execute('INSERT INTO study_program (name, code) VALUES (?, ?)', (name, code))
                db.commit()
                flash(f'Studijski program "{name}" je dodan.', 'success')
                return redirect(url_for('study_program.index'))
            except db.IntegrityError:
                flash(f'Šifra "{code}" već postoji.', 'danger')
    return render_template('study_program/form.html')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    db = get_db()
    program = db.execute('SELECT * FROM study_program WHERE id = ?', (id,)).fetchone()
    if program is None:
        flash('Studijski program nije pronađen.', 'danger')
        return redirect(url_for('study_program.index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        code = request.form['code'].strip()
        if not name or not code:
            flash('Sva polja su obavezna.', 'danger')
        else:
            try:
                db.execute('UPDATE study_program SET name = ?, code = ? WHERE id = ?', (name, code, id))
                db.commit()
                flash('Studijski program je ažuriran.', 'success')
                return redirect(url_for('study_program.index'))
            except db.IntegrityError:
                flash(f'Šifra "{code}" već postoji.', 'danger')
    return render_template('study_program/form.html', program=program)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    db = get_db()
    db.execute('DELETE FROM study_program WHERE id = ?', (id,))
    db.commit()
    flash('Studijski program je obrisan.', 'success')
    return redirect(url_for('study_program.index'))
