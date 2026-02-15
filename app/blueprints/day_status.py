from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.models import DAY_STATUSES

bp = Blueprint('day_status', __name__)


@bp.route('/')
def index():
    db = get_db()
    academic_years = db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall()
    selected_year_id = request.args.get('academic_year_id', type=int)

    statuses = []
    if selected_year_id:
        statuses = db.execute(
            'SELECT * FROM day_status WHERE academic_year_id = ? ORDER BY date',
            (selected_year_id,)
        ).fetchall()

    return render_template(
        'day_status/index.html',
        academic_years=academic_years,
        selected_year_id=selected_year_id,
        statuses=statuses,
        day_statuses=DAY_STATUSES,
    )


@bp.route('/create', methods=['POST'])
def create():
    db = get_db()
    academic_year_id = request.form['academic_year_id']
    date = request.form['date'].strip()
    status = request.form['status']
    note = request.form.get('note', '').strip()

    if not date or not status:
        flash('Datum i status su obavezni.', 'danger')
        return redirect(url_for('day_status.index', academic_year_id=academic_year_id))

    try:
        db.execute(
            'INSERT INTO day_status (academic_year_id, date, status, note) VALUES (?, ?, ?, ?)',
            (academic_year_id, date, status, note)
        )
        db.commit()
        flash(f'Datum {date} je označen kao {status}.', 'success')
    except db.IntegrityError:
        flash(f'Datum {date} već postoji za ovu akademsku godinu.', 'danger')

    return redirect(url_for('day_status.index', academic_year_id=academic_year_id))


@bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    db = get_db()
    entry = db.execute('SELECT academic_year_id FROM day_status WHERE id = ?', (id,)).fetchone()
    academic_year_id = entry['academic_year_id'] if entry else None
    db.execute('DELETE FROM day_status WHERE id = ?', (id,))
    db.commit()
    flash('Datum je uklonjen.', 'success')
    return redirect(url_for('day_status.index', academic_year_id=academic_year_id))
