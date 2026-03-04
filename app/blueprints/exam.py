import json
import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from app.db import get_db
from app.auth import login_required, api_login_required
from app.models import (
    DAYS, DAYS_ALL, TIMES_IZVANREDNI,
    check_exam_conflicts, date_to_day_of_week,
    sort_classrooms, sort_professors,
)
from app.audit import log_audit

bp = Blueprint('exam', __name__)

HISTORY_LIMIT = 30


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
        return iso_date or ''


def _exam_snapshot(db, entry_id):
    """Napravi JSON snapshot ispitnog roka s imenima za čitljiv prikaz."""
    row = db.execute('''
        SELECT ee.*,
               p.title, p.first_name, p.last_name,
               cl.name as classroom_name
        FROM exam_entry ee
        JOIN professor p ON ee.professor_id = p.id
        JOIN classroom cl ON ee.classroom_id = cl.id
        WHERE ee.id = ?
    ''', (entry_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    prof = f"{d.pop('title', '')} {d.pop('first_name', '')} {d.pop('last_name', '')}".strip()
    d['_professor_name'] = prof
    d['_classroom_name'] = d.pop('classroom_name')
    d['_day_name'] = DAYS.get(d['day_of_week'], '')
    d['_date_display'] = _format_date(d.get('date', ''))
    return d


def _log_exam_history(db, entry_id, action, old_data, new_data):
    """Zapiši promjenu u exam_history i očisti stare zapise."""
    db.execute('''
        INSERT INTO exam_history (entry_id, action, old_data, new_data, user_id, user_name)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        entry_id, action,
        json.dumps(old_data, ensure_ascii=False) if old_data else None,
        json.dumps(new_data, ensure_ascii=False) if new_data else None,
        session.get('user_id'),
        session.get('user_display_name', 'Nepoznat'),
    ))
    db.execute('''
        DELETE FROM exam_history
        WHERE id NOT IN (SELECT id FROM exam_history ORDER BY id DESC LIMIT ?)
    ''', (HISTORY_LIMIT,))


def get_exam_form_data(entry_start=None, entry_end=None):
    """Dohvati podatke za dropdown-e u formi ispitnih rokova."""
    db = get_db()
    times = list(TIMES_IZVANREDNI)
    extra = set()
    if entry_start and entry_start not in times:
        extra.add(entry_start)
    if entry_end and entry_end not in times:
        extra.add(entry_end)
    if extra:
        times = sorted(set(times) | extra)
    default_ay = db.execute('SELECT id FROM academic_year WHERE is_default = 1').fetchone()
    return {
        'default_academic_year_id': default_ay['id'] if default_ay else None,
        'academic_years': db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall(),
        'professors': sort_professors(db.execute('SELECT * FROM professor').fetchall()),
        'classrooms': sort_classrooms(db.execute('SELECT * FROM classroom').fetchall()),
        'days': DAYS_ALL,
        'times': times,
    }


@bp.route('/')
@login_required
def index():
    db = get_db()
    query = '''
        SELECT ee.*,
               p.first_name, p.last_name, p.title,
               cl.name as classroom_name,
               ay.name as academic_year_name
        FROM exam_entry ee
        JOIN professor p ON ee.professor_id = p.id
        JOIN classroom cl ON ee.classroom_id = cl.id
        JOIN academic_year ay ON ee.academic_year_id = ay.id
        ORDER BY ee.id DESC
    '''
    entries = db.execute(query).fetchall()
    return render_template('exam/index.html', entries=entries, days=DAYS_ALL)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        db = get_db()
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        # Datum je obavezan
        raw_date = request.form.get('entry_date', '').strip()
        if not raw_date:
            flash('Datum je obavezan.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))
        entry_date = _parse_date(raw_date)
        if not entry_date:
            flash('Neispravan format datuma. Koristite dd.mm.YYYY. format.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))

        day_of_week = date_to_day_of_week(entry_date)

        # Samo pon-sub (1-6)
        if not day_of_week or day_of_week > 6:
            flash('Ispitni rokovi su dopušteni samo od ponedjeljka do subote.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))

        if end_time <= start_time:
            flash('Završno vrijeme mora biti nakon početnog.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))

        entry_data = {
            'academic_year_id': request.form['academic_year_id'],
            'professor_id': request.form['professor_id'],
            'classroom_id': request.form['classroom_id'],
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'date': entry_date,
            'note': request.form.get('note', '').strip() or None,
        }

        conflicts = check_exam_conflicts(entry_data)
        confirmed = request.form.get('confirm_conflicts') == '1'

        if conflicts and not confirmed:
            entry_data_display = dict(entry_data)
            if entry_data_display.get('date'):
                entry_data_display['date'] = _format_date(entry_data_display['date'])
            return render_template('exam/form.html', entry=entry_data_display,
                                   conflicts=conflicts, **get_exam_form_data(start_time, end_time))

        has_conflict = 1 if (conflicts and confirmed) else 0
        cursor = db.execute('''
            INSERT INTO exam_entry
            (academic_year_id, date, day_of_week, start_time, end_time,
             professor_id, classroom_id, note, has_conflict, is_published)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            entry_data['academic_year_id'], entry_date, day_of_week,
            start_time, end_time,
            entry_data['professor_id'], entry_data['classroom_id'],
            entry_data['note'], has_conflict,
        ))
        new_id = cursor.lastrowid
        new_snapshot = _exam_snapshot(db, new_id)
        _log_exam_history(db, new_id, 'create', None, new_snapshot)
        desc = f'Dodan ispitni rok: {new_snapshot.get("_professor_name", "?")} ({new_snapshot.get("_date_display", "?")}, {new_snapshot.get("start_time", "")}-{new_snapshot.get("end_time", "")})' if new_snapshot else 'Dodan ispitni rok'
        log_audit('create', 'exam_entry', desc, new_id, db)
        db.commit()
        flash('Ispitni rok je dodan.', 'success')
        return redirect(url_for('exam.index'))

    return render_template('exam/form.html', **get_exam_form_data())


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    entry = db.execute('SELECT * FROM exam_entry WHERE id = ?', (id,)).fetchone()
    if entry is None:
        flash('Ispitni rok nije pronađen.', 'danger')
        return redirect(url_for('exam.index'))

    if request.method == 'POST':
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        raw_date = request.form.get('entry_date', '').strip()
        if not raw_date:
            flash('Datum je obavezan.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))
        entry_date = _parse_date(raw_date)
        if not entry_date:
            flash('Neispravan format datuma. Koristite dd.mm.YYYY. format.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))

        day_of_week = date_to_day_of_week(entry_date)
        if not day_of_week or day_of_week > 6:
            flash('Ispitni rokovi su dopušteni samo od ponedjeljka do subote.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))

        if end_time <= start_time:
            flash('Završno vrijeme mora biti nakon početnog.', 'danger')
            return render_template('exam/form.html', entry=request.form,
                                   **get_exam_form_data(start_time, end_time))

        entry_data = {
            'academic_year_id': request.form['academic_year_id'],
            'professor_id': request.form['professor_id'],
            'classroom_id': request.form['classroom_id'],
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'date': entry_date,
            'note': request.form.get('note', '').strip() or None,
        }

        conflicts = check_exam_conflicts(entry_data, exclude_id=id)
        confirmed = request.form.get('confirm_conflicts') == '1'

        if conflicts and not confirmed:
            entry_data_display = dict(entry_data)
            if entry_data_display.get('date'):
                entry_data_display['date'] = _format_date(entry_data_display['date'])
            return render_template('exam/form.html', entry=entry_data_display,
                                   conflicts=conflicts, **get_exam_form_data(start_time, end_time))

        has_conflict = 1 if (conflicts and confirmed) else 0
        old_snapshot = _exam_snapshot(db, id)
        db.execute('''
            UPDATE exam_entry SET
                academic_year_id = ?, date = ?, day_of_week = ?,
                start_time = ?, end_time = ?,
                professor_id = ?, classroom_id = ?,
                note = ?, has_conflict = ?, is_published = 0
            WHERE id = ?
        ''', (
            entry_data['academic_year_id'], entry_date, day_of_week,
            start_time, end_time,
            entry_data['professor_id'], entry_data['classroom_id'],
            entry_data['note'], has_conflict, id,
        ))
        new_snapshot = _exam_snapshot(db, id)
        _log_exam_history(db, id, 'update', old_snapshot, new_snapshot)
        desc = f'Uređen ispitni rok: {new_snapshot.get("_professor_name", "?")} ({new_snapshot.get("_date_display", "?")}, {new_snapshot.get("start_time", "")}-{new_snapshot.get("end_time", "")})' if new_snapshot else 'Uređen ispitni rok'
        log_audit('update', 'exam_entry', desc, id, db)
        db.commit()
        flash('Ispitni rok je ažuriran.', 'success')
        return redirect(url_for('exam.index'))

    entry_dict = dict(entry)
    if entry_dict.get('date'):
        entry_dict['date'] = _format_date(entry_dict['date'])
    return render_template('exam/form.html', entry=entry_dict,
                           **get_exam_form_data(entry['start_time'], entry['end_time']))


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    old_snapshot = _exam_snapshot(db, id)
    if old_snapshot:
        _log_exam_history(db, id, 'delete', old_snapshot, None)
        desc = f'Obrisan ispitni rok: {old_snapshot.get("_professor_name", "?")} ({old_snapshot.get("_date_display", "?")}, {old_snapshot.get("start_time", "")}-{old_snapshot.get("end_time", "")})'
        log_audit('delete', 'exam_entry', desc, id, db)
    db.execute('DELETE FROM exam_entry WHERE id = ?', (id,))
    db.commit()
    flash('Ispitni rok je obrisan.', 'success')
    return redirect(url_for('exam.index'))


@bp.route('/api/check-conflicts', methods=['POST'])
@api_login_required
def api_check_conflicts():
    data = request.get_json()
    if not data:
        return jsonify({'conflicts': []})

    entry_date = data.get('entry_date', '').strip()
    if entry_date:
        parsed = _parse_date(entry_date)
        if parsed:
            entry_date = parsed
            day_of_week = date_to_day_of_week(parsed)
        else:
            return jsonify({'conflicts': []})
    else:
        return jsonify({'conflicts': []})

    entry_data = {
        'academic_year_id': data.get('academic_year_id'),
        'professor_id': data.get('professor_id'),
        'classroom_id': data.get('classroom_id'),
        'day_of_week': day_of_week,
        'start_time': data.get('start_time'),
        'end_time': data.get('end_time'),
        'date': entry_date,
    }

    if not all([entry_data['academic_year_id'], entry_data['start_time'], entry_data['end_time']]):
        return jsonify({'conflicts': []})

    exclude_id = data.get('entry_id')
    conflicts = check_exam_conflicts(entry_data, exclude_id=exclude_id)
    return jsonify({'conflicts': conflicts})


@bp.route('/api/free-classrooms')
@login_required
def api_free_classrooms():
    """Dohvati slobodne učionice za termin ispitnog roka."""
    db = get_db()
    academic_year_id = request.args.get('academic_year_id')
    entry_date = request.args.get('date', '')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if not all([academic_year_id, entry_date, start_time, end_time]):
        return jsonify({'classrooms': []})

    # Zauzete učionice iz exam_entry
    exam_occupied = db.execute('''
        SELECT DISTINCT classroom_id FROM exam_entry
        WHERE academic_year_id = ? AND date = ?
        AND start_time < ? AND end_time > ?
    ''', [academic_year_id, entry_date, end_time, start_time]).fetchall()

    occupied_ids = set(r['classroom_id'] for r in exam_occupied)

    all_classrooms = sort_classrooms(db.execute('SELECT * FROM classroom').fetchall())
    free = [{'id': c['id'], 'name': c['name']} for c in all_classrooms if c['id'] not in occupied_ids]
    return jsonify({'classrooms': free})


@bp.route('/history')
@login_required
def history():
    db = get_db()
    rows = db.execute(
        'SELECT * FROM exam_history ORDER BY id DESC LIMIT ?', (HISTORY_LIMIT,)
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item['old_data'] = json.loads(item['old_data']) if item['old_data'] else None
        item['new_data'] = json.loads(item['new_data']) if item['new_data'] else None
        data = item['old_data'] or item['new_data'] or {}
        item['_professor_name'] = data.get('_professor_name', '?')
        item['_day_name'] = data.get('_day_name', '?')
        item['_date_display'] = data.get('_date_display', '')
        item['_start_time'] = data.get('start_time', '')
        item['_end_time'] = data.get('end_time', '')
        item['_classroom_name'] = data.get('_classroom_name', '')
        items.append(item)
    return render_template('exam/history.html', items=items, days=DAYS_ALL)


def _undo_single(db, row):
    """Poništi jednu promjenu ispitnog roka."""
    action = row['action']
    old_data = json.loads(row['old_data']) if row['old_data'] else None
    entry_id = row['entry_id']

    if action == 'create':
        db.execute('DELETE FROM exam_entry WHERE id = ?', (entry_id,))
    elif action == 'update':
        if not old_data:
            return False
        exists = db.execute('SELECT id FROM exam_entry WHERE id = ?', (entry_id,)).fetchone()
        if not exists:
            return False
        db.execute('''
            UPDATE exam_entry SET
                academic_year_id = ?, date = ?, day_of_week = ?,
                start_time = ?, end_time = ?,
                professor_id = ?, classroom_id = ?,
                note = ?, has_conflict = ?, is_published = ?
            WHERE id = ?
        ''', (
            old_data.get('academic_year_id'), old_data.get('date', ''),
            old_data.get('day_of_week'), old_data.get('start_time'),
            old_data.get('end_time'), old_data.get('professor_id'),
            old_data.get('classroom_id'), old_data.get('note'),
            old_data.get('has_conflict', 0), old_data.get('is_published', 0),
            entry_id,
        ))
    elif action == 'delete':
        if not old_data:
            return False
        db.execute('''
            INSERT INTO exam_entry
            (academic_year_id, date, day_of_week, start_time, end_time,
             professor_id, classroom_id, note, has_conflict, is_published)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            old_data.get('academic_year_id'), old_data.get('date', ''),
            old_data.get('day_of_week'), old_data.get('start_time'),
            old_data.get('end_time'), old_data.get('professor_id'),
            old_data.get('classroom_id'), old_data.get('note'),
            old_data.get('has_conflict', 0), old_data.get('is_published', 0),
        ))
    return True


_MAX_UNDO_BACKUPS = 5


def _create_undo_backup():
    """Kreiraj backup baze prije poništavanja."""
    db_path = current_app.config['DATABASE']
    if not os.path.exists(db_path):
        return None
    backup_dir = os.path.join(os.path.dirname(db_path), 'undo_backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    backup_name = f'raspored_pre_undo_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_name)
    try:
        shutil.copy2(db_path, backup_path)
    except OSError:
        return None
    existing = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith('raspored_pre_undo_') and f.endswith('.db')],
        reverse=True,
    )
    for old in existing[_MAX_UNDO_BACKUPS:]:
        try:
            os.remove(os.path.join(backup_dir, old))
        except OSError:
            pass
    return backup_name


@bp.route('/history/<int:id>/undo', methods=['POST'])
@login_required
def history_undo(id):
    db = get_db()
    rows = db.execute(
        'SELECT * FROM exam_history WHERE id >= ? ORDER BY id DESC', (id,)
    ).fetchall()
    if not rows:
        flash('Zapis povijesti nije pronađen.', 'danger')
        return redirect(url_for('exam.history'))

    backup_name = _create_undo_backup()

    count = 0
    for row in rows:
        if _undo_single(db, row):
            count += 1

    db.execute('DELETE FROM exam_history WHERE id >= ?', (id,))
    log_audit('undo', 'exam_entry', f'Poništeno {count} promjena ispitnih rokova', db=db)
    db.commit()

    if count == 1:
        flash('Poništena je 1 promjena.', 'success')
    else:
        flash(f'Poništeno je {count} promjena.', 'success')

    if backup_name:
        flash(f'Backup baze kreiran prije poništavanja: {backup_name}', 'info')

    return redirect(url_for('exam.history'))
