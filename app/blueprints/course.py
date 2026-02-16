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


@bp.route('/import', methods=['POST'])
def import_bulk():
    from openpyxl import load_workbook
    import io

    if 'file' not in request.files:
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('course.index'))

    file = request.files['file']
    if file.filename == '':
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('course.index'))

    try:
        wb = load_workbook(io.BytesIO(file.read()), read_only=True)
        ws = wb.active
        db = get_db()
        added = 0
        skipped = 0
        duplicates = 0

        for row in ws.iter_rows(min_row=1, values_only=True):
            if not row or len(row) < 2:
                continue
            # Format: šifra, naziv kolegija
            cells = [str(c).strip() if c is not None else '' for c in row[:2]]
            code = cells[0]
            name = cells[1]

            if not code or not name:
                skipped += 1
                continue

            # Skip header row
            if code.lower() in ('šifra', 'sifra', 'code') and name.lower() in ('naziv', 'name', 'naziv kolegija'):
                continue

            try:
                db.execute(
                    'INSERT INTO course (name, code) VALUES (?, ?)',
                    (name, code)
                )
                added += 1
            except db.IntegrityError:
                duplicates += 1

        db.commit()
        wb.close()
        msg = f'Uvezeno {added} kolegija.'
        if duplicates:
            msg += f' Preskočeno {duplicates} duplikata.'
        if skipped:
            msg += f' Preskočeno {skipped} neispravnih redaka.'
        flash(msg, 'success')
    except Exception as e:
        flash(f'Greška pri uvozu: {e}', 'danger')

    return redirect(url_for('course.index'))
