from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.auth import login_required, super_admin_required
from app.audit import log_audit

bp = Blueprint('academic_year', __name__)


@bp.route('/')
@login_required
def index():
    db = get_db()
    years = db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall()
    return render_template('academic_year/index.html', years=years)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Naziv akademske godine je obavezan.', 'danger')
        else:
            db = get_db()
            try:
                cursor = db.execute('INSERT INTO academic_year (name) VALUES (?)', (name,))
                log_audit('create', 'academic_year', f'Dodana akademska godina "{name}"', cursor.lastrowid, db)
                db.commit()
                flash(f'Akademska godina "{name}" je dodana.', 'success')
                return redirect(url_for('academic_year.index'))
            except db.IntegrityError:
                flash(f'Akademska godina "{name}" već postoji.', 'danger')
    return render_template('academic_year/form.html')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    year = db.execute('SELECT * FROM academic_year WHERE id = ?', (id,)).fetchone()
    if year is None:
        flash('Akademska godina nije pronađena.', 'danger')
        return redirect(url_for('academic_year.index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Naziv akademske godine je obavezan.', 'danger')
        else:
            try:
                db.execute('UPDATE academic_year SET name = ? WHERE id = ?', (name, id))
                log_audit('update', 'academic_year', f'Ažurirana akademska godina "{year["name"]}" → "{name}"', id, db)
                db.commit()
                flash(f'Akademska godina je ažurirana.', 'success')
                return redirect(url_for('academic_year.index'))
            except db.IntegrityError:
                flash(f'Akademska godina "{name}" već postoji.', 'danger')
    return render_template('academic_year/form.html', year=year)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    year = db.execute('SELECT * FROM academic_year WHERE id = ?', (id,)).fetchone()
    if year and year['is_default']:
        flash('Zadana akademska godina se ne može obrisati. Prvo postavite drugu godinu kao zadanu.', 'danger')
        return redirect(url_for('academic_year.index'))
    log_audit('delete', 'academic_year', f'Obrisana akademska godina "{year["name"]}"' if year else f'Obrisana akademska godina ID={id}', id, db)
    db.execute('DELETE FROM academic_year WHERE id = ?', (id,))
    db.commit()
    flash('Akademska godina je obrisana.', 'success')
    return redirect(url_for('academic_year.index'))


@bp.route('/<int:id>/copy', methods=['GET', 'POST'])
@login_required
def copy(id):
    db = get_db()
    source = db.execute('SELECT * FROM academic_year WHERE id = ?', (id,)).fetchone()
    if source is None:
        flash('Izvorna akademska godina nije pronađena.', 'danger')
        return redirect(url_for('academic_year.index'))

    years = db.execute('SELECT * FROM academic_year WHERE id != ? ORDER BY name DESC', (id,)).fetchall()

    if request.method == 'POST':
        target_id = request.form.get('target_id', type=int)
        if not target_id:
            flash('Odaberite ciljnu akademsku godinu.', 'danger')
        else:
            target = db.execute('SELECT * FROM academic_year WHERE id = ?', (target_id,)).fetchone()
            if target is None:
                flash('Ciljna akademska godina nije pronađena.', 'danger')
            else:
                entries = db.execute('SELECT * FROM schedule_entry WHERE academic_year_id = ?', (id,)).fetchall()
                if not entries:
                    flash(f'Nema stavki rasporeda u godini "{source["name"]}" za kopiranje.', 'info')
                else:
                    for e in entries:
                        db.execute('''
                            INSERT INTO schedule_entry
                            (academic_year_id, study_program_id, semester_type, semester_number,
                             course_id, group_name, module_name, teaching_form, professor_id, classroom_id,
                             date, day_of_week, start_time, end_time, week_type, has_conflict, is_published, note)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
                        ''', (
                            target_id, e['study_program_id'], e['semester_type'], e['semester_number'],
                            e['course_id'], e['group_name'], e['module_name'], e['teaching_form'],
                            e['professor_id'], e['classroom_id'],
                            e['date'], e['day_of_week'], e['start_time'], e['end_time'], e['week_type'],
                            e['note'],
                        ))

                    # Copy day_status entries
                    day_statuses = db.execute('SELECT * FROM day_status WHERE academic_year_id = ?', (id,)).fetchall()
                    for ds in day_statuses:
                        try:
                            db.execute(
                                'INSERT INTO day_status (academic_year_id, day_of_week, status, note) VALUES (?, ?, ?, ?)',
                                (target_id, ds['day_of_week'], ds['status'], ds['note'])
                            )
                        except db.IntegrityError:
                            pass

                    # Copy day_status_date entries
                    date_statuses = db.execute('SELECT * FROM day_status_date WHERE academic_year_id = ?', (id,)).fetchall()
                    for ds in date_statuses:
                        try:
                            db.execute(
                                'INSERT INTO day_status_date (academic_year_id, date, status, note) VALUES (?, ?, ?, ?)',
                                (target_id, ds['date'], ds['status'], ds['note'])
                            )
                        except db.IntegrityError:
                            pass

                    copied_extras = len(day_statuses) + len(date_statuses)
                    log_audit('copy', 'academic_year',
                              f'Kopirano {len(entries)} stavki + {copied_extras} statusa dana iz "{source["name"]}" u "{target["name"]}"',
                              target_id, db)
                    db.commit()
                    flash(f'Kopirano {len(entries)} stavki rasporeda iz "{source["name"]}" u "{target["name"]}".', 'success')
                    return redirect(url_for('academic_year.index'))

    return render_template('academic_year/copy.html', source=source, years=years)


@bp.route('/<int:id>/set-default', methods=['POST'])
@super_admin_required
def set_default(id):
    db = get_db()
    year = db.execute('SELECT * FROM academic_year WHERE id = ?', (id,)).fetchone()
    if year is None:
        flash('Akademska godina nije pronađena.', 'danger')
        return redirect(url_for('academic_year.index'))
    db.execute('UPDATE academic_year SET is_default = 0')
    db.execute('UPDATE academic_year SET is_default = 1 WHERE id = ?', (id,))
    log_audit('update', 'academic_year', f'Postavljena zadana akademska godina "{year["name"]}"', id, db)
    db.commit()
    flash(f'Akademska godina "{year["name"]}" je postavljena kao zadana.', 'success')
    return redirect(url_for('academic_year.index'))
