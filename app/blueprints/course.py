from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db

bp = Blueprint('course', __name__)


@bp.route('/')
def index():
    db = get_db()
    courses = db.execute('SELECT * FROM course ORDER BY name').fetchall()
    return render_template('course/index.html', courses=courses)


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
                db.execute('INSERT INTO course (name, code) VALUES (?, ?)', (name, code))
                db.commit()
                flash(f'Kolegij "{name}" je dodan.', 'success')
                return redirect(url_for('course.index'))
            except db.IntegrityError:
                flash(f'Šifra kolegija "{code}" već postoji.', 'danger')
    return render_template('course/form.html')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    db = get_db()
    course = db.execute('SELECT * FROM course WHERE id = ?', (id,)).fetchone()
    if course is None:
        flash('Kolegij nije pronađen.', 'danger')
        return redirect(url_for('course.index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        code = request.form['code'].strip()
        if not name or not code:
            flash('Sva polja su obavezna.', 'danger')
        else:
            try:
                db.execute('UPDATE course SET name = ?, code = ? WHERE id = ?', (name, code, id))
                db.commit()
                flash('Kolegij je ažuriran.', 'success')
                return redirect(url_for('course.index'))
            except db.IntegrityError:
                flash(f'Šifra kolegija "{code}" već postoji.', 'danger')
    return render_template('course/form.html', course=course)


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    db = get_db()
    db.execute('DELETE FROM course WHERE id = ?', (id,))
    db.commit()
    flash('Kolegij je obrisan.', 'success')
    return redirect(url_for('course.index'))
