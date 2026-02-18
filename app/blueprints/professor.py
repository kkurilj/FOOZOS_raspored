from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.auth import login_required
from app.models import PROFESSOR_TITLES
from app.audit import log_audit

bp = Blueprint('professor', __name__)


def _all_titles():
    """Return predefined titles merged with any custom titles already in the database."""
    db = get_db()
    db_titles = [r[0] for r in db.execute(
        'SELECT DISTINCT title FROM professor WHERE title != "" ORDER BY title'
    ).fetchall()]
    seen = set(PROFESSOR_TITLES)
    merged = list(PROFESSOR_TITLES)
    for t in db_titles:
        if t not in seen:
            merged.append(t)
            seen.add(t)
    return merged


@bp.route('/')
@login_required
def index():
    db = get_db()
    professors = db.execute(
        'SELECT * FROM professor ORDER BY last_name, first_name'
    ).fetchall()
    return render_template('professor/index.html', professors=professors)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        title = request.form['title'].strip()
        if not first_name or not last_name:
            flash('Ime i prezime su obavezni.', 'danger')
        else:
            db = get_db()
            try:
                cursor = db.execute(
                    'INSERT INTO professor (first_name, last_name, title) VALUES (?, ?, ?)',
                    (first_name, last_name, title)
                )
                full_name = f'{title} {first_name} {last_name}'.strip()
                log_audit('create', 'professor', f'Dodan profesor "{full_name}"', cursor.lastrowid, db)
                db.commit()
                flash(f'Profesor "{full_name}" je dodan.', 'success')
                return redirect(url_for('professor.index'))
            except db.IntegrityError:
                flash(f'Profesor "{title} {first_name} {last_name}" već postoji.'.strip(), 'danger')
    return render_template('professor/form.html', titles=_all_titles())


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    professor = db.execute('SELECT * FROM professor WHERE id = ?', (id,)).fetchone()
    if professor is None:
        flash('Profesor nije pronađen.', 'danger')
        return redirect(url_for('professor.index'))

    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        title = request.form['title'].strip()
        if not first_name or not last_name:
            flash('Ime i prezime su obavezni.', 'danger')
        else:
            try:
                db.execute(
                    'UPDATE professor SET first_name = ?, last_name = ?, title = ? WHERE id = ?',
                    (first_name, last_name, title, id)
                )
                full_name = f'{title} {first_name} {last_name}'.strip()
                log_audit('update', 'professor', f'Ažuriran profesor "{full_name}"', id, db)
                db.commit()
                flash('Profesor je ažuriran.', 'success')
                return redirect(url_for('professor.index'))
            except db.IntegrityError:
                flash(f'Profesor "{title} {first_name} {last_name}" već postoji.'.strip(), 'danger')
    return render_template('professor/form.html', professor=professor, titles=_all_titles())


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    prof = db.execute('SELECT title, first_name, last_name FROM professor WHERE id = ?', (id,)).fetchone()
    if prof:
        full_name = f'{prof["title"]} {prof["first_name"]} {prof["last_name"]}'.strip()
        log_audit('delete', 'professor', f'Obrisan profesor "{full_name}"', id, db)
    db.execute('DELETE FROM professor WHERE id = ?', (id,))
    db.commit()
    flash('Profesor je obrisan.', 'success')
    return redirect(url_for('professor.index'))


@bp.route('/import', methods=['POST'])
@login_required
def import_bulk():
    from app.models import read_excel_rows

    if 'file' not in request.files:
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('professor.index'))

    file = request.files['file']
    if file.filename == '':
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('professor.index'))

    try:
        rows = read_excel_rows(file)
        db = get_db()
        added = 0
        skipped = 0
        duplicates = 0

        for row in rows:
            if not row or len(row) < 2:
                continue
            # Format: titula, ime, prezime
            cells = [str(c).strip() if c is not None else '' for c in row[:3]]
            if len(cells) == 2:
                title, first_name, last_name = '', cells[0], cells[1]
            else:
                title, first_name, last_name = cells[0], cells[1], cells[2]

            if not first_name or not last_name:
                skipped += 1
                continue

            # Skip header row
            if first_name.lower() in ('ime', 'first_name', 'name') and last_name.lower() in ('prezime', 'last_name', 'surname'):
                continue

            try:
                db.execute(
                    'INSERT INTO professor (first_name, last_name, title) VALUES (?, ?, ?)',
                    (first_name, last_name, title)
                )
                added += 1
            except db.IntegrityError:
                duplicates += 1

        if added:
            log_audit('import', 'professor', f'Uvezeno {added} profesora iz Excel datoteke', db=db)
        db.commit()
        msg = f'Uvezeno {added} profesora.'
        if duplicates:
            msg += f' Preskočeno {duplicates} duplikata.'
        if skipped:
            msg += f' Preskočeno {skipped} neispravnih redaka.'
        flash(msg, 'success')
    except Exception:
        flash('Greška pri uvozu. Provjerite format datoteke.', 'danger')

    return redirect(url_for('professor.index'))
