from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.auth import login_required
from app.models import STUDY_MODES

bp = Blueprint('study_program', __name__)


@bp.route('/')
def index():
    db = get_db()
    programs = db.execute('SELECT * FROM study_program ORDER BY name, element').fetchall()
    return render_template('study_program/index.html', programs=programs)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name'].strip()
        code = request.form['code'].strip()
        study_mode = request.form.get('study_mode', 'redoviti')
        element = request.form.get('element', '').strip()
        if not name or not code:
            flash('Naziv i šifra su obavezni.', 'danger')
        else:
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO study_program (name, code, study_mode, element) VALUES (?, ?, ?, ?)',
                    (name, code, study_mode, element)
                )
                db.commit()
                flash(f'Studijski program "{name}" je dodan.', 'success')
                return redirect(url_for('study_program.index'))
            except db.IntegrityError:
                flash(f'Kombinacija šifre "{code}" i elementa "{element}" već postoji.', 'danger')
    return render_template('study_program/form.html', study_modes=STUDY_MODES)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    program = db.execute('SELECT * FROM study_program WHERE id = ?', (id,)).fetchone()
    if program is None:
        flash('Studijski program nije pronađen.', 'danger')
        return redirect(url_for('study_program.index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        code = request.form['code'].strip()
        study_mode = request.form.get('study_mode', 'redoviti')
        element = request.form.get('element', '').strip()
        if not name or not code:
            flash('Naziv i šifra su obavezni.', 'danger')
        else:
            try:
                db.execute(
                    'UPDATE study_program SET name = ?, code = ?, study_mode = ?, element = ? WHERE id = ?',
                    (name, code, study_mode, element, id)
                )
                db.commit()
                flash('Studijski program je ažuriran.', 'success')
                return redirect(url_for('study_program.index'))
            except db.IntegrityError:
                flash(f'Kombinacija šifre "{code}" i elementa "{element}" već postoji.', 'danger')
    return render_template('study_program/form.html', program=program, study_modes=STUDY_MODES)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    db.execute('DELETE FROM study_program WHERE id = ?', (id,))
    db.commit()
    flash('Studijski program je obrisan.', 'success')
    return redirect(url_for('study_program.index'))


@bp.route('/import', methods=['POST'])
@login_required
def import_bulk():
    from app.models import read_excel_rows

    if 'file' not in request.files:
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('study_program.index'))

    file = request.files['file']
    if file.filename == '':
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('study_program.index'))

    try:
        rows = read_excel_rows(file)
        db = get_db()
        added = 0
        skipped = 0
        duplicates = 0

        for row in rows:
            if not row or len(row) < 2:
                continue
            # Format: šifra, naziv, način studiranja, element studija
            cells = [str(c).strip() if c is not None else '' for c in row[:4]]
            code = cells[0]
            name = cells[1]
            study_mode = cells[2].lower() if len(cells) > 2 and cells[2] else 'redoviti'
            element = cells[3] if len(cells) > 3 else ''

            if not code or not name:
                skipped += 1
                continue

            # Skip header row
            if code.lower() in ('šifra', 'sifra', 'code') and name.lower() in ('naziv', 'name'):
                continue

            if study_mode not in ('redoviti', 'izvanredni'):
                study_mode = 'redoviti'

            try:
                db.execute(
                    'INSERT INTO study_program (name, code, study_mode, element) VALUES (?, ?, ?, ?)',
                    (name, code, study_mode, element)
                )
                added += 1
            except db.IntegrityError:
                duplicates += 1

        db.commit()
        msg = f'Uvezeno {added} programa.'
        if duplicates:
            msg += f' Preskočeno {duplicates} duplikata.'
        if skipped:
            msg += f' Preskočeno {skipped} neispravnih redaka.'
        flash(msg, 'success')
    except Exception as e:
        flash(f'Greška pri uvozu: {e}', 'danger')

    return redirect(url_for('study_program.index'))
