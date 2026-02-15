from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.db import get_db
from app.models import (
    DAYS, TIMES, WEEK_TYPES, GROUPS, MODULES, SEMESTER_TYPES,
    check_conflicts, date_to_day_of_week
)

bp = Blueprint('schedule', __name__)


def get_form_data():
    """Dohvati podatke za dropdown-e u formi."""
    db = get_db()
    return {
        'academic_years': db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall(),
        'study_programs': db.execute('SELECT * FROM study_program ORDER BY name').fetchall(),
        'courses': db.execute('SELECT * FROM course ORDER BY name').fetchall(),
        'professors': db.execute('SELECT * FROM professor ORDER BY last_name, first_name').fetchall(),
        'classrooms': db.execute('SELECT * FROM classroom ORDER BY name').fetchall(),
        'day_statuses': db.execute('SELECT * FROM day_status ORDER BY date').fetchall(),
        'days': DAYS,
        'times': TIMES,
        'week_types': WEEK_TYPES,
        'groups': GROUPS,
        'modules': MODULES,
        'semester_types': SEMESTER_TYPES,
    }


@bp.route('/')
def index():
    db = get_db()

    query = '''
        SELECT se.*, c.name as course_name,
               p.first_name, p.last_name, p.title,
               cl.name as classroom_name,
               sp.name as program_name,
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
def create():
    if request.method == 'POST':
        date = request.form['date'].strip()
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        if not date:
            flash('Datum je obavezan.', 'danger')
            return render_template('schedule/form.html', entry=request.form, **get_form_data())

        if end_time <= start_time:
            flash('Završno vrijeme mora biti nakon početnog.', 'danger')
            return render_template('schedule/form.html', entry=request.form, **get_form_data())

        day_of_week = date_to_day_of_week(date)

        entry_data = {
            'academic_year_id': request.form['academic_year_id'],
            'study_program_id': request.form['study_program_id'],
            'semester_type': request.form['semester_type'],
            'semester_number': request.form['semester_number'],
            'course_id': request.form['course_id'],
            'group_name': request.form['group_name'],
            'module_name': request.form.get('module_name') or None,
            'professor_id': request.form['professor_id'],
            'classroom_id': request.form['classroom_id'],
            'date': date,
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'week_type': request.form['week_type'],
        }

        conflicts = check_conflicts(entry_data)
        confirmed = request.form.get('confirm_conflicts') == '1'

        if conflicts and not confirmed:
            return render_template('schedule/form.html', entry=entry_data,
                                   conflicts=conflicts, **get_form_data())

        db = get_db()
        db.execute('''
            INSERT INTO schedule_entry
            (academic_year_id, study_program_id, semester_type, semester_number,
             course_id, group_name, module_name, professor_id, classroom_id,
             date, day_of_week, start_time, end_time, week_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_data['academic_year_id'], entry_data['study_program_id'],
            entry_data['semester_type'], entry_data['semester_number'],
            entry_data['course_id'], entry_data['group_name'],
            entry_data['module_name'], entry_data['professor_id'],
            entry_data['classroom_id'], entry_data['date'],
            entry_data['day_of_week'], entry_data['start_time'],
            entry_data['end_time'], entry_data['week_type'],
        ))
        db.commit()
        flash('Stavka rasporeda je dodana.', 'success')
        return redirect(url_for('schedule.index'))

    return render_template('schedule/form.html', **get_form_data())


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    db = get_db()
    entry = db.execute('SELECT * FROM schedule_entry WHERE id = ?', (id,)).fetchone()
    if entry is None:
        flash('Stavka rasporeda nije pronađena.', 'danger')
        return redirect(url_for('schedule.index'))

    if request.method == 'POST':
        date = request.form['date'].strip()
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        if not date:
            flash('Datum je obavezan.', 'danger')
            return render_template('schedule/form.html', entry=entry, **get_form_data())

        if end_time <= start_time:
            flash('Završno vrijeme mora biti nakon početnog.', 'danger')
            return render_template('schedule/form.html', entry=request.form, **get_form_data())

        day_of_week = date_to_day_of_week(date)

        entry_data = {
            'academic_year_id': request.form['academic_year_id'],
            'study_program_id': request.form['study_program_id'],
            'semester_type': request.form['semester_type'],
            'semester_number': request.form['semester_number'],
            'course_id': request.form['course_id'],
            'group_name': request.form['group_name'],
            'module_name': request.form.get('module_name') or None,
            'professor_id': request.form['professor_id'],
            'classroom_id': request.form['classroom_id'],
            'date': date,
            'day_of_week': day_of_week,
            'start_time': start_time,
            'end_time': end_time,
            'week_type': request.form['week_type'],
        }

        conflicts = check_conflicts(entry_data, exclude_id=id)
        confirmed = request.form.get('confirm_conflicts') == '1'

        if conflicts and not confirmed:
            return render_template('schedule/form.html', entry=entry_data,
                                   conflicts=conflicts, **get_form_data())

        db.execute('''
            UPDATE schedule_entry SET
                academic_year_id = ?, study_program_id = ?, semester_type = ?,
                semester_number = ?, course_id = ?, group_name = ?,
                module_name = ?, professor_id = ?, classroom_id = ?,
                date = ?, day_of_week = ?, start_time = ?, end_time = ?,
                week_type = ?
            WHERE id = ?
        ''', (
            entry_data['academic_year_id'], entry_data['study_program_id'],
            entry_data['semester_type'], entry_data['semester_number'],
            entry_data['course_id'], entry_data['group_name'],
            entry_data['module_name'], entry_data['professor_id'],
            entry_data['classroom_id'], entry_data['date'],
            entry_data['day_of_week'], entry_data['start_time'],
            entry_data['end_time'], entry_data['week_type'], id,
        ))
        db.commit()
        flash('Stavka rasporeda je ažurirana.', 'success')
        return redirect(url_for('schedule.index'))

    return render_template('schedule/form.html', entry=entry, **get_form_data())


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    db = get_db()
    db.execute('DELETE FROM schedule_entry WHERE id = ?', (id,))
    db.commit()
    flash('Stavka rasporeda je obrisana.', 'success')
    return redirect(url_for('schedule.index'))


@bp.route('/api/move', methods=['POST'])
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

    if new_end > '20:45':
        return jsonify({'success': False, 'error': 'Predavanje prelazi radno vrijeme (20:45).'}), 400

    # Izracunaj novi datum na temelju originalnog datuma i novog dana
    orig_date = datetime.strptime(entry['date'], '%Y-%m-%d')
    orig_dow = orig_date.isoweekday()
    day_diff = new_day - orig_dow
    new_date = orig_date + timedelta(days=day_diff)
    new_date_str = new_date.strftime('%Y-%m-%d')

    entry_data = dict(entry)
    entry_data['day_of_week'] = new_day
    entry_data['start_time'] = new_start
    entry_data['end_time'] = new_end
    entry_data['date'] = new_date_str

    conflicts = check_conflicts(entry_data, exclude_id=entry_id)
    if conflicts and not force:
        return jsonify({'success': False, 'conflicts': conflicts})

    db.execute('''
        UPDATE schedule_entry SET
            day_of_week = ?, start_time = ?, end_time = ?, date = ?
        WHERE id = ?
    ''', (new_day, new_start, new_end, new_date_str, entry_id))
    db.commit()

    return jsonify({'success': True})


@bp.route('/api/check-conflicts', methods=['POST'])
def api_check_conflicts():
    """Provjeri konflikte za stavku (AJAX za formu)."""
    data = request.get_json()
    entry_id = data.get('entry_id')

    required = ['date', 'start_time', 'end_time', 'academic_year_id',
                 'professor_id', 'classroom_id', 'study_program_id',
                 'semester_number', 'group_name']
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
        'date': data['date'],
        'day_of_week': date_to_day_of_week(data['date']),
        'start_time': data['start_time'],
        'end_time': data['end_time'],
        'week_type': data.get('week_type', 'kontinuirano'),
    }

    conflicts = check_conflicts(entry_data, exclude_id=entry_id)
    return jsonify({'conflicts': conflicts})
