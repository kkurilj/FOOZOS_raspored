from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.auth import login_required
from app.models import PROFESSOR_TITLES

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
            db.execute(
                'INSERT INTO professor (first_name, last_name, title) VALUES (?, ?, ?)',
                (first_name, last_name, title)
            )
            db.commit()
            flash(f'Profesor "{title} {first_name} {last_name}" je dodan.'.strip(), 'success')
            return redirect(url_for('professor.index'))
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
            db.execute(
                'UPDATE professor SET first_name = ?, last_name = ?, title = ? WHERE id = ?',
                (first_name, last_name, title, id)
            )
            db.commit()
            flash('Profesor je ažuriran.', 'success')
            return redirect(url_for('professor.index'))
    return render_template('professor/form.html', professor=professor, titles=_all_titles())


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
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

            db.execute(
                'INSERT INTO professor (first_name, last_name, title) VALUES (?, ?, ?)',
                (first_name, last_name, title)
            )
            added += 1

        db.commit()
        flash(f'Uvezeno {added} profesora.' + (f' Preskočeno {skipped} redaka.' if skipped else ''), 'success')
    except Exception as e:
        flash(f'Greška pri uvozu: {e}', 'danger')

    return redirect(url_for('professor.index'))
