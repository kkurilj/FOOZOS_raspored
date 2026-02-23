from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.auth import login_required
from app.models import STUDY_MODES
from app.audit import log_audit

bp = Blueprint('study_program', __name__)


def _parse_custom_time_fields(form):
    """Parsira i validira custom time polja iz forme. Vraća (fields, error)."""
    raw_start = form.get('custom_start_time', '').strip()
    raw_end = form.get('custom_end_time', '').strip()
    raw_minutes = form.get('custom_slot_minutes', '').strip()

    start = raw_start or None
    end = raw_end or None
    try:
        minutes = int(raw_minutes) if raw_minutes else None
    except (ValueError, TypeError):
        return None, 'Trajanje termina mora biti cijeli broj.'

    has_any = any([start, end, minutes])
    has_all = all([start, end, minutes])

    if has_any and not has_all:
        return None, 'Ako definirate vlastite termine, sva tri polja su obavezna (početak, završetak, trajanje).'

    if has_all:
        try:
            s = datetime.strptime(start, '%H:%M')
            e = datetime.strptime(end, '%H:%M')
            if s.minute % 15 != 0 or e.minute % 15 != 0:
                return None, 'Vrijeme mora biti na okrugle minute (00, 15, 30, 45).'
            if e <= s:
                return None, 'Završno vrijeme mora biti nakon početnog.'
            if start < '08:00':
                return None, 'Početno vrijeme ne može biti prije 08:00.'
            if end > '21:00':
                return None, 'Završno vrijeme ne može biti nakon 21:00.'
        except ValueError:
            return None, 'Neispravan format vremena. Koristite HH:MM format.'
        if minutes < 15 or minutes > 120:
            return None, 'Trajanje termina mora biti između 15 i 120 minuta.'

    return {'custom_start_time': start, 'custom_end_time': end, 'custom_slot_minutes': minutes}, None


@bp.route('/')
@login_required
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
        custom, error = _parse_custom_time_fields(request.form)
        if not name or not code:
            flash('Naziv i šifra su obavezni.', 'danger')
        elif error:
            flash(error, 'danger')
        else:
            db = get_db()
            try:
                cursor = db.execute(
                    '''INSERT INTO study_program (name, code, study_mode, element,
                       custom_start_time, custom_end_time, custom_slot_minutes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (name, code, study_mode, element,
                     custom['custom_start_time'], custom['custom_end_time'], custom['custom_slot_minutes'])
                )
                log_audit('create', 'study_program', f'Dodan studijski program "{name}" ({code})', cursor.lastrowid, db)
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
        custom, error = _parse_custom_time_fields(request.form)
        if not name or not code:
            flash('Naziv i šifra su obavezni.', 'danger')
        elif error:
            flash(error, 'danger')
        else:
            try:
                db.execute(
                    '''UPDATE study_program SET name = ?, code = ?, study_mode = ?, element = ?,
                       custom_start_time = ?, custom_end_time = ?, custom_slot_minutes = ?
                       WHERE id = ?''',
                    (name, code, study_mode, element,
                     custom['custom_start_time'], custom['custom_end_time'], custom['custom_slot_minutes'], id)
                )
                log_audit('update', 'study_program', f'Ažuriran studijski program "{name}" ({code})', id, db)
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
    prog = db.execute('SELECT name, code FROM study_program WHERE id = ?', (id,)).fetchone()
    log_audit('delete', 'study_program', f'Obrisan studijski program "{prog["name"]}" ({prog["code"]})' if prog else f'Obrisan studijski program ID={id}', id, db)
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
    if not file.filename.lower().endswith(('.xls', '.xlsx')):
        flash('Samo Excel datoteke (.xls, .xlsx) su dozvoljene.', 'danger')
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

        if added:
            log_audit('import', 'study_program', f'Uvezeno {added} studijskih programa iz Excel datoteke', db=db)
        db.commit()
        msg = f'Uvezeno {added} programa.'
        if duplicates:
            msg += f' Preskočeno {duplicates} duplikata.'
        if skipped:
            msg += f' Preskočeno {skipped} neispravnih redaka.'
        flash(msg, 'success')
    except Exception:
        flash('Greška pri uvozu. Provjerite format datoteke.', 'danger')

    return redirect(url_for('study_program.index'))
