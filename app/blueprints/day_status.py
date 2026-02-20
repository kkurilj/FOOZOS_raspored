from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.db import get_db
from app.auth import login_required, api_login_required
from app.models import DAYS, DAY_STATUSES
from app.audit import log_audit


def _parse_date(date_str):
    """Parse dd.mm.YYYY. or dd.mm.YYYY to ISO YYYY-MM-DD."""
    date_str = date_str.strip().rstrip('.')
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').strftime('%Y-%m-%d')
    except ValueError:
        return None


def _format_date(iso_date):
    """Format ISO YYYY-MM-DD to dd.mm.YYYY."""
    try:
        return datetime.strptime(iso_date, '%Y-%m-%d').strftime('%d.%m.%Y.')
    except (ValueError, TypeError):
        return iso_date

bp = Blueprint('day_status', __name__)


@bp.route('/')
@login_required
def index():
    db = get_db()
    academic_years = db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall()
    selected_year_id = request.args.get('academic_year_id', type=int)

    # Default to the default academic year if none selected
    if selected_year_id is None and 'academic_year_id' not in request.args:
        default_row = db.execute('SELECT id FROM academic_year WHERE is_default = 1').fetchone()
        if default_row:
            selected_year_id = default_row['id']

    statuses = []
    date_statuses = []
    if selected_year_id:
        statuses = db.execute(
            'SELECT * FROM day_status WHERE academic_year_id = ? ORDER BY day_of_week',
            (selected_year_id,)
        ).fetchall()
        date_statuses = db.execute(
            'SELECT * FROM day_status_date WHERE academic_year_id = ? ORDER BY date',
            (selected_year_id,)
        ).fetchall()

    return render_template(
        'day_status/index.html',
        academic_years=academic_years,
        selected_year_id=selected_year_id,
        statuses=statuses,
        date_statuses=date_statuses,
        day_statuses=DAY_STATUSES,
        days=DAYS,
        format_date=_format_date,
    )


@bp.route('/create', methods=['POST'])
@login_required
def create():
    db = get_db()
    academic_year_id = request.form['academic_year_id']
    mode = request.form.get('mode', 'day_of_week')
    status = request.form['status']
    note = request.form.get('note', '').strip()

    if mode == 'specific_date':
        raw_date = request.form.get('specific_date', '').strip()
        if not raw_date or not status:
            flash('Datum i status su obavezni.', 'danger')
            return redirect(url_for('day_status.index', academic_year_id=academic_year_id))
        iso_date = _parse_date(raw_date)
        if not iso_date:
            flash('Neispravan format datuma. Koristite dd.mm.YYYY. format.', 'danger')
            return redirect(url_for('day_status.index', academic_year_id=academic_year_id))
        display_date = _format_date(iso_date)
        try:
            cursor = db.execute(
                'INSERT INTO day_status_date (academic_year_id, date, status, note) VALUES (?, ?, ?, ?)',
                (academic_year_id, iso_date, status, note)
            )
            log_audit('create', 'day_status_date', f'Dodan status datuma: {display_date} → {status}', cursor.lastrowid, db)
            db.commit()
            flash(f'{display_date} je označen kao {status}.', 'success')
        except db.IntegrityError:
            flash(f'{display_date} već ima status za ovu akademsku godinu.', 'danger')
    else:
        day_of_week = request.form.get('day_of_week', type=int)
        if not day_of_week or not status:
            flash('Dan i status su obavezni.', 'danger')
            return redirect(url_for('day_status.index', academic_year_id=academic_year_id))
        try:
            cursor = db.execute(
                'INSERT INTO day_status (academic_year_id, day_of_week, status, note) VALUES (?, ?, ?, ?)',
                (academic_year_id, day_of_week, status, note)
            )
            log_audit('create', 'day_status', f'Dodan status dana: {DAYS[day_of_week]} → {status}', cursor.lastrowid, db)
            db.commit()
            flash(f'{DAYS[day_of_week]} je označen kao {status}.', 'success')
        except db.IntegrityError:
            flash(f'{DAYS[day_of_week]} već ima status za ovu akademsku godinu.', 'danger')

    return redirect(url_for('day_status.index', academic_year_id=academic_year_id))


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    entry = db.execute('SELECT academic_year_id, day_of_week, status FROM day_status WHERE id = ?', (id,)).fetchone()
    academic_year_id = entry['academic_year_id'] if entry else None
    if entry:
        log_audit('delete', 'day_status', f'Uklonjen status dana: {DAYS.get(entry["day_of_week"], "?")} ({entry["status"]})', id, db)
    db.execute('DELETE FROM day_status WHERE id = ?', (id,))
    db.commit()
    flash('Status dana je uklonjen.', 'success')
    return redirect(url_for('day_status.index', academic_year_id=academic_year_id))


@bp.route('/date/<int:id>/delete', methods=['POST'])
@login_required
def delete_date(id):
    db = get_db()
    entry = db.execute('SELECT academic_year_id, date, status FROM day_status_date WHERE id = ?', (id,)).fetchone()
    academic_year_id = entry['academic_year_id'] if entry else None
    if entry:
        log_audit('delete', 'day_status_date', f'Uklonjen status datuma: {entry["date"]} ({entry["status"]})', id, db)
    db.execute('DELETE FROM day_status_date WHERE id = ?', (id,))
    db.commit()
    flash('Status datuma je uklonjen.', 'success')
    return redirect(url_for('day_status.index', academic_year_id=academic_year_id))


@bp.route('/api/set', methods=['POST'])
@api_login_required
def api_set():
    """Set or update day status (from timetable dblclick)."""
    data = request.get_json()
    academic_year_id = data.get('academic_year_id')
    day_of_week = data.get('day_of_week')
    specific_date = data.get('date')  # ISO format YYYY-MM-DD
    status = data.get('status')
    note = data.get('note', '')

    if not academic_year_id:
        return jsonify({'success': False, 'error': 'Nedostaju podaci.'}), 400

    db = get_db()

    # Date-specific status
    if specific_date:
        if not status:
            db.execute(
                'DELETE FROM day_status_date WHERE academic_year_id = ? AND date = ?',
                (academic_year_id, specific_date)
            )
            log_audit('delete', 'day_status_date', f'Uklonjen status datuma: {specific_date}', db=db)
            db.commit()
            return jsonify({'success': True, 'cleared': True})

        if status not in DAY_STATUSES:
            return jsonify({'success': False, 'error': 'Nevažeći status.'}), 400

        existing = db.execute(
            'SELECT id FROM day_status_date WHERE academic_year_id = ? AND date = ?',
            (academic_year_id, specific_date)
        ).fetchone()

        if existing:
            db.execute('UPDATE day_status_date SET status = ?, note = ? WHERE id = ?',
                        (status, note, existing['id']))
            log_audit('update', 'day_status_date', f'Ažuriran status datuma: {specific_date} → {status}', existing['id'], db)
        else:
            db.execute('INSERT INTO day_status_date (academic_year_id, date, status, note) VALUES (?, ?, ?, ?)',
                        (academic_year_id, specific_date, status, note))
            log_audit('create', 'day_status_date', f'Dodan status datuma: {specific_date} → {status}', db=db)
        db.commit()
        return jsonify({'success': True})

    # Day-of-week status (existing behavior)
    if not day_of_week:
        return jsonify({'success': False, 'error': 'Nedostaju podaci.'}), 400

    if not status:
        db.execute(
            'DELETE FROM day_status WHERE academic_year_id = ? AND day_of_week = ?',
            (academic_year_id, day_of_week)
        )
        log_audit('delete', 'day_status', f'Uklonjen status dana: {DAYS.get(day_of_week, "?")}', db=db)
        db.commit()
        return jsonify({'success': True, 'cleared': True})

    if status not in DAY_STATUSES:
        return jsonify({'success': False, 'error': 'Nevažeći status.'}), 400

    existing = db.execute(
        'SELECT id FROM day_status WHERE academic_year_id = ? AND day_of_week = ?',
        (academic_year_id, day_of_week)
    ).fetchone()

    if existing:
        db.execute('UPDATE day_status SET status = ?, note = ? WHERE id = ?',
                    (status, note, existing['id']))
        log_audit('update', 'day_status', f'Ažuriran status dana: {DAYS.get(day_of_week, "?")} → {status}', existing['id'], db)
    else:
        db.execute('INSERT INTO day_status (academic_year_id, day_of_week, status, note) VALUES (?, ?, ?, ?)',
                    (academic_year_id, day_of_week, status, note))
        log_audit('create', 'day_status', f'Dodan status dana: {DAYS.get(day_of_week, "?")} → {status}', db=db)
    db.commit()
    return jsonify({'success': True})
