import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.db import get_db
from app.auth import login_required, api_login_required
from app.models import (
    DAYS, WEEK_TYPES, GROUPS, MODULES, SEMESTER_TYPES, TEACHING_FORMS,
    TIMES_REDOVITI, TIMES_IZVANREDNI,
    check_conflicts, date_to_day_of_week
)
from app.audit import log_audit

bp = Blueprint('schedule', __name__)

HISTORY_LIMIT = 15


def _entry_snapshot(db, entry_id):
    """Napravi JSON snapshot stavke s imenima za čitljiv prikaz."""
    row = db.execute('''
        SELECT se.*, c.name as course_name,
               p.title, p.first_name, p.last_name,
               cl.name as classroom_name
        FROM schedule_entry se
        JOIN course c ON se.course_id = c.id
        JOIN professor p ON se.professor_id = p.id
        JOIN classroom cl ON se.classroom_id = cl.id
        WHERE se.id = ?
    ''', (entry_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    prof = f"{d.pop('title', '')} {d.pop('first_name', '')} {d.pop('last_name', '')}".strip()
    d['_course_name'] = d.pop('course_name')
    d['_professor_name'] = prof
    d['_classroom_name'] = d.pop('classroom_name')
    d['_day_name'] = DAYS.get(d['day_of_week'], '')
    return d


def _log_history(db, entry_id, action, old_data, new_data):
    """Zapiši promjenu u schedule_history i očisti stare zapise."""
    db.execute('''
        INSERT INTO schedule_history (entry_id, action, old_data, new_data, user_id, user_name)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        entry_id, action,
        json.dumps(old_data, ensure_ascii=False) if old_data else None,
        json.dumps(new_data, ensure_ascii=False) if new_data else None,
        session.get('user_id'),
        session.get('user_display_name', 'Nepoznat'),
    ))
    # Zadrži samo zadnjih HISTORY_LIMIT zapisa
    db.execute('''
        DELETE FROM schedule_history
        WHERE id NOT IN (SELECT id FROM schedule_history ORDER BY id DESC LIMIT ?)
    ''', (HISTORY_LIMIT,))


def get_form_data(study_mode=None, entry_start=None, entry_end=None):
    """Dohvati podatke za dropdown-e u formi."""
    db = get_db()
    times = list(TIMES_IZVANREDNI if study_mode == 'izvanredni' else TIMES_REDOVITI)
    # Uključi stvarna vremena stavke ako nisu u standardnoj listi
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
        'study_programs': db.execute('SELECT * FROM study_program ORDER BY name, element').fetchall(),
        'courses': db.execute('SELECT * FROM course ORDER BY name').fetchall(),
        'professors': db.execute('SELECT * FROM professor ORDER BY last_name, first_name').fetchall(),
        'classrooms': db.execute('SELECT * FROM classroom ORDER BY name').fetchall(),
        'days': DAYS,
        'times': times,
        'times_redoviti': TIMES_REDOVITI,
        'times_izvanredni': TIMES_IZVANREDNI,
        'week_types': WEEK_TYPES,
        'groups': GROUPS,
        'modules': MODULES,
        'semester_types': SEMESTER_TYPES,
        'teaching_forms': TEACHING_FORMS,
    }


@bp.route('/')
@login_required
def index():
    db = get_db()

    query = '''
        SELECT se.*, c.name as course_name,
               p.first_name, p.last_name, p.title,
               cl.name as classroom_name,
               sp.name as program_name, sp.element as program_element, sp.study_mode,
               ay.name as academic_year_name
        FROM schedule_entry se
        JOIN course c ON se.course_id = c.id
        JOIN professor p ON se.professor_id = p.id
        JOIN classroom cl ON se.classroom_id = cl.id
        JOIN study_program sp ON se.study_program_id = sp.id
        JOIN academic_year ay ON se.academic_year_id = ay.id
        ORDER BY ay.name DESC, sp.name, se.semester_number, se.day_of_week, se.start_time
    '''
    entries = db.execute(query).fetchall()
    return render_template('schedule/index.html', entries=entries, days=DAYS)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        db = get_db()
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        # Dohvati study_mode iz studijskog programa
        program = db.execute('SELECT study_mode FROM study_program WHERE id = ?',
                             (request.form['study_program_id'],)).fetchone()
        study_mode = program['study_mode'] if program else 'redoviti'

        # Za izvanredne: datum je obavezan, day_of_week se računa iz datuma
        entry_date = ''
        if study_mode == 'izvanredni':
            entry_date = request.form.get('entry_date', '')
            if not entry_date:
                flash('Datum je obavezan za izvanredne studente.', 'danger')
                return render_template('schedule/form.html', entry=request.form,
                                       **get_form_data(study_mode, start_time, end_time))
            day_of_week = date_to_day_of_week(entry_date)
        else:
            day_of_week = request.form.get('day_of_week', type=int)

        if not day_of_week:
            flash('Dan je obavezan.', 'danger')
            return render_template('schedule/form.html', entry=request.form,
                                   **get_form_data(study_mode, start_time, end_time))

        if end_time <= start_time:
            flash('Završno vrijeme mora biti nakon početnog.', 'danger')
            return render_template('schedule/form.html', entry=request.form,
                                   **get_form_data(study_mode, start_time, end_time))

        entry_data = {
            'academic_year_id': request.form['academic_year_id'],
            'study_program_id': request.form['study_program_id'],
            'semester_type': request.form['semester_type'],
            'semester_number': request.form['semester_number'],
            'course_id': request.form['course_id'],
            'group_name': request.form.get('group_name') or None,
            'module_name': request.form.get('module_name') or None,
            'teaching_form': request.form.get('teaching_form', 'predavanja'),
            'professor_id': request.form['professor_id'],
            'classroom_id': request.form['classroom_id'],
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'week_type': request.form['week_type'],
            'date': entry_date,
        }

        conflicts = check_conflicts(entry_data)
        confirmed = request.form.get('confirm_conflicts') == '1'

        if conflicts and not confirmed:
            return render_template('schedule/form.html', entry=entry_data,
                                   conflicts=conflicts, **get_form_data(study_mode, start_time, end_time))

        has_conflict = 1 if (conflicts and confirmed) else 0
        cursor = db.execute('''
            INSERT INTO schedule_entry
            (academic_year_id, study_program_id, semester_type, semester_number,
             course_id, group_name, module_name, teaching_form, professor_id, classroom_id,
             date, day_of_week, start_time, end_time, week_type, has_conflict, is_published)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ''', (
            entry_data['academic_year_id'], entry_data['study_program_id'],
            entry_data['semester_type'], entry_data['semester_number'],
            entry_data['course_id'], entry_data['group_name'],
            entry_data['module_name'], entry_data['teaching_form'],
            entry_data['professor_id'],
            entry_data['classroom_id'], entry_date,
            entry_data['day_of_week'], entry_data['start_time'],
            entry_data['end_time'], entry_data['week_type'], has_conflict,
        ))
        new_id = cursor.lastrowid
        new_snapshot = _entry_snapshot(db, new_id)
        _log_history(db, new_id, 'create', None, new_snapshot)
        desc = f'Dodana stavka rasporeda: {new_snapshot.get("_course_name", "?")} ({new_snapshot.get("_day_name", "?")}, {new_snapshot.get("start_time", "")}-{new_snapshot.get("end_time", "")})' if new_snapshot else 'Dodana stavka rasporeda'
        log_audit('create', 'schedule_entry', desc, new_id, db)
        db.commit()
        flash('Stavka rasporeda je dodana.', 'success')
        return redirect(url_for('schedule.index'))

    return render_template('schedule/form.html', **get_form_data())


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    entry = db.execute('SELECT * FROM schedule_entry WHERE id = ?', (id,)).fetchone()
    if entry is None:
        flash('Stavka rasporeda nije pronađena.', 'danger')
        return redirect(url_for('schedule.index'))

    if request.method == 'POST':
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        # Dohvati study_mode iz studijskog programa
        program = db.execute('SELECT study_mode FROM study_program WHERE id = ?',
                             (request.form['study_program_id'],)).fetchone()
        study_mode = program['study_mode'] if program else 'redoviti'

        entry_date = ''
        if study_mode == 'izvanredni':
            entry_date = request.form.get('entry_date', '')
            if not entry_date:
                flash('Datum je obavezan za izvanredne studente.', 'danger')
                return render_template('schedule/form.html', entry=request.form,
                                       **get_form_data(study_mode, start_time, end_time))
            day_of_week = date_to_day_of_week(entry_date)
        else:
            day_of_week = request.form.get('day_of_week', type=int)

        if not day_of_week:
            flash('Dan je obavezan.', 'danger')
            return render_template('schedule/form.html', entry=entry,
                                   **get_form_data(study_mode, start_time, end_time))

        if end_time <= start_time:
            flash('Završno vrijeme mora biti nakon početnog.', 'danger')
            return render_template('schedule/form.html', entry=request.form,
                                   **get_form_data(study_mode, start_time, end_time))

        entry_data = {
            'academic_year_id': request.form['academic_year_id'],
            'study_program_id': request.form['study_program_id'],
            'semester_type': request.form['semester_type'],
            'semester_number': request.form['semester_number'],
            'course_id': request.form['course_id'],
            'group_name': request.form.get('group_name') or None,
            'module_name': request.form.get('module_name') or None,
            'teaching_form': request.form.get('teaching_form', 'predavanja'),
            'professor_id': request.form['professor_id'],
            'classroom_id': request.form['classroom_id'],
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'week_type': request.form['week_type'],
            'date': entry_date,
        }

        conflicts = check_conflicts(entry_data, exclude_id=id)
        confirmed = request.form.get('confirm_conflicts') == '1'

        if conflicts and not confirmed:
            return render_template('schedule/form.html', entry=entry_data,
                                   conflicts=conflicts, **get_form_data(study_mode, start_time, end_time))

        has_conflict = 1 if (conflicts and confirmed) else 0
        old_snapshot = _entry_snapshot(db, id)
        db.execute('''
            UPDATE schedule_entry SET
                academic_year_id = ?, study_program_id = ?, semester_type = ?,
                semester_number = ?, course_id = ?, group_name = ?,
                module_name = ?, teaching_form = ?, professor_id = ?, classroom_id = ?,
                date = ?, day_of_week = ?, start_time = ?, end_time = ?,
                week_type = ?, has_conflict = ?, is_published = 0
            WHERE id = ?
        ''', (
            entry_data['academic_year_id'], entry_data['study_program_id'],
            entry_data['semester_type'], entry_data['semester_number'],
            entry_data['course_id'], entry_data['group_name'],
            entry_data['module_name'], entry_data['teaching_form'],
            entry_data['professor_id'],
            entry_data['classroom_id'], entry_date,
            entry_data['day_of_week'], entry_data['start_time'],
            entry_data['end_time'], entry_data['week_type'], has_conflict, id,
        ))
        new_snapshot = _entry_snapshot(db, id)
        _log_history(db, id, 'update', old_snapshot, new_snapshot)
        desc = f'Ažurirana stavka rasporeda: {(new_snapshot or {}).get("_course_name", "?")}' if new_snapshot else 'Ažurirana stavka rasporeda'
        log_audit('update', 'schedule_entry', desc, id, db)
        db.commit()
        flash('Stavka rasporeda je ažurirana.', 'success')
        return redirect(url_for('schedule.index'))

    # Dohvati study_mode za ispravnu listu vremena
    program = db.execute('SELECT study_mode FROM study_program WHERE id = ?',
                         (entry['study_program_id'],)).fetchone()
    entry_study_mode = program['study_mode'] if program else 'redoviti'
    return render_template('schedule/form.html', entry=entry,
                           **get_form_data(entry_study_mode, entry['start_time'], entry['end_time']))


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    old_snapshot = _entry_snapshot(db, id)
    if old_snapshot:
        _log_history(db, id, 'delete', old_snapshot, None)
        desc = f'Obrisana stavka rasporeda: {old_snapshot.get("_course_name", "?")} ({old_snapshot.get("_day_name", "?")}, {old_snapshot.get("start_time", "")}-{old_snapshot.get("end_time", "")})'
        log_audit('delete', 'schedule_entry', desc, id, db)
    db.execute('DELETE FROM schedule_entry WHERE id = ?', (id,))
    db.commit()
    flash('Stavka rasporeda je obrisana.', 'success')
    return redirect(url_for('schedule.index'))


@bp.route('/api/move', methods=['POST'])
@api_login_required
def api_move():
    """Premjesti stavku rasporeda na novi dan/vrijeme (drag & drop)."""
    data = request.get_json()
    entry_id = data.get('entry_id')
    new_day = data.get('day_of_week')
    new_start = data.get('start_time')
    force = data.get('force', False)

    db = get_db()
    entry = db.execute('SELECT * FROM schedule_entry WHERE id = ?', (entry_id,)).fetchone()
    if not entry:
        return jsonify({'success': False, 'error': 'Stavka nije pronađena.'}), 404

    # Izracunaj novo end_time na temelju trajanja
    old_start = datetime.strptime(entry['start_time'], '%H:%M')
    old_end = datetime.strptime(entry['end_time'], '%H:%M')
    duration = old_end - old_start

    new_start_dt = datetime.strptime(new_start, '%H:%M')
    new_end_dt = new_start_dt + duration
    new_end = new_end_dt.strftime('%H:%M')

    # Provjeri study_mode za max end time
    program = db.execute('SELECT study_mode FROM study_program WHERE id = ?',
                         (entry['study_program_id'],)).fetchone()
    study_mode = program['study_mode'] if program else 'redoviti'
    max_end = '21:00' if study_mode == 'izvanredni' else '19:30'

    if new_end > max_end:
        return jsonify({'success': False, 'error': f'Predavanje prelazi radno vrijeme ({max_end}).'}), 400

    entry_data = dict(entry)
    entry_data['day_of_week'] = new_day
    entry_data['start_time'] = new_start
    entry_data['end_time'] = new_end

    conflicts = check_conflicts(entry_data, exclude_id=entry_id)
    if conflicts and not force:
        return jsonify({'success': False, 'conflicts': conflicts})

    has_conflict = 1 if (conflicts and force) else 0
    old_snapshot = _entry_snapshot(db, entry_id)
    db.execute('''
        UPDATE schedule_entry SET
            day_of_week = ?, start_time = ?, end_time = ?, has_conflict = ?, is_published = 0
        WHERE id = ?
    ''', (new_day, new_start, new_end, has_conflict, entry_id))
    new_snapshot = _entry_snapshot(db, entry_id)
    _log_history(db, entry_id, 'move', old_snapshot, new_snapshot)
    course_name = (old_snapshot or {}).get('_course_name', '?')
    old_day = (old_snapshot or {}).get('_day_name', '?')
    new_day_name = DAYS.get(new_day, '?')
    log_audit('update', 'schedule_entry', f'Premještena stavka "{course_name}" ({old_day} → {new_day_name}, {new_start}-{new_end})', entry_id, db)
    db.commit()

    return jsonify({'success': True})


@bp.route('/api/check-conflicts', methods=['POST'])
@api_login_required
def api_check_conflicts():
    """Provjeri konflikte za stavku (AJAX za formu)."""
    data = request.get_json()
    entry_id = data.get('entry_id')

    required = ['day_of_week', 'start_time', 'end_time', 'academic_year_id',
                 'professor_id', 'classroom_id', 'study_program_id',
                 'semester_number']
    if not all(data.get(f) for f in required):
        return jsonify({'conflicts': []})

    entry_data = {
        'academic_year_id': data.get('academic_year_id'),
        'study_program_id': data.get('study_program_id'),
        'semester_type': data.get('semester_type'),
        'semester_number': data.get('semester_number'),
        'course_id': data.get('course_id'),
        'group_name': data.get('group_name'),
        'professor_id': data.get('professor_id'),
        'classroom_id': data.get('classroom_id'),
        'day_of_week': int(data['day_of_week']),
        'start_time': data['start_time'],
        'end_time': data['end_time'],
        'week_type': data.get('week_type', 'kontinuirano'),
    }

    conflicts = check_conflicts(entry_data, exclude_id=entry_id)
    return jsonify({'conflicts': conflicts})


@bp.route('/history')
@login_required
def history():
    db = get_db()
    rows = db.execute(
        'SELECT * FROM schedule_history ORDER BY id DESC LIMIT ?', (HISTORY_LIMIT,)
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item['old_data'] = json.loads(item['old_data']) if item['old_data'] else None
        item['new_data'] = json.loads(item['new_data']) if item['new_data'] else None
        # Koristi snapshot za prikaz opisa
        data = item['old_data'] or item['new_data'] or {}
        item['_course_name'] = data.get('_course_name', '?')
        item['_day_name'] = data.get('_day_name', '?')
        item['_start_time'] = data.get('start_time', '')
        item['_end_time'] = data.get('end_time', '')
        item['_professor_name'] = data.get('_professor_name', '')
        item['_classroom_name'] = data.get('_classroom_name', '')
        items.append(item)
    return render_template('schedule/history.html', items=items, days=DAYS)


def _undo_single(db, row):
    """Poništi jednu promjenu iz povijesti. Vraća True ako je uspjelo."""
    action = row['action']
    old_data = json.loads(row['old_data']) if row['old_data'] else None
    entry_id = row['entry_id']

    if action == 'create':
        db.execute('DELETE FROM schedule_entry WHERE id = ?', (entry_id,))

    elif action in ('update', 'move'):
        if not old_data:
            return False
        exists = db.execute('SELECT id FROM schedule_entry WHERE id = ?', (entry_id,)).fetchone()
        if not exists:
            return False
        db.execute('''
            UPDATE schedule_entry SET
                academic_year_id = ?, study_program_id = ?, semester_type = ?,
                semester_number = ?, course_id = ?, group_name = ?,
                module_name = ?, teaching_form = ?, professor_id = ?, classroom_id = ?,
                date = ?, day_of_week = ?, start_time = ?, end_time = ?,
                week_type = ?, has_conflict = ?
            WHERE id = ?
        ''', (
            old_data.get('academic_year_id'), old_data.get('study_program_id'),
            old_data.get('semester_type'), old_data.get('semester_number'),
            old_data.get('course_id'), old_data.get('group_name'),
            old_data.get('module_name'), old_data.get('teaching_form', 'predavanja'),
            old_data.get('professor_id'), old_data.get('classroom_id'),
            old_data.get('date', ''), old_data.get('day_of_week'),
            old_data.get('start_time'), old_data.get('end_time'),
            old_data.get('week_type'), old_data.get('has_conflict', 0), entry_id,
        ))

    elif action == 'delete':
        if not old_data:
            return False
        db.execute('''
            INSERT INTO schedule_entry
            (academic_year_id, study_program_id, semester_type, semester_number,
             course_id, group_name, module_name, teaching_form, professor_id, classroom_id,
             date, day_of_week, start_time, end_time, week_type, has_conflict)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            old_data.get('academic_year_id'), old_data.get('study_program_id'),
            old_data.get('semester_type'), old_data.get('semester_number'),
            old_data.get('course_id'), old_data.get('group_name'),
            old_data.get('module_name'), old_data.get('teaching_form', 'predavanja'),
            old_data.get('professor_id'), old_data.get('classroom_id'),
            old_data.get('date', ''), old_data.get('day_of_week'),
            old_data.get('start_time'), old_data.get('end_time'),
            old_data.get('week_type'), old_data.get('has_conflict', 0),
        ))

    return True


@bp.route('/history/<int:id>/undo', methods=['POST'])
@login_required
def history_undo(id):
    db = get_db()
    # Dohvati odabranu promjenu i sve novije (id >= odabrani), od najnovije prema starijoj
    rows = db.execute(
        'SELECT * FROM schedule_history WHERE id >= ? ORDER BY id DESC', (id,)
    ).fetchall()
    if not rows:
        flash('Zapis povijesti nije pronađen.', 'danger')
        return redirect(url_for('schedule.history'))

    count = 0
    for row in rows:
        if _undo_single(db, row):
            count += 1

    # Obriši sve poništene zapise
    db.execute('DELETE FROM schedule_history WHERE id >= ?', (id,))
    log_audit('undo', 'schedule_entry', f'Poništeno {count} promjena rasporeda', db=db)
    db.commit()

    if count == 1:
        flash('Poništena je 1 promjena.', 'success')
    else:
        flash(f'Poništeno je {count} promjena.', 'success')
    return redirect(url_for('schedule.history'))
