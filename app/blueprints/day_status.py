from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.models import DAYS, DAY_STATUSES

bp = Blueprint('day_status', __name__)


@bp.route('/')
def index():
    db = get_db()
    academic_years = db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall()
    selected_year_id = request.args.get('academic_year_id', type=int)

    statuses = {}
    if selected_year_id:
        rows = db.execute(
            'SELECT * FROM day_status WHERE academic_year_id = ?', (selected_year_id,)
        ).fetchall()
        for row in rows:
            statuses[row['day_of_week']] = row

    return render_template(
        'day_status/index.html',
        academic_years=academic_years,
        selected_year_id=selected_year_id,
        statuses=statuses,
        days=DAYS,
        day_statuses=DAY_STATUSES,
    )


@bp.route('/save', methods=['POST'])
def save():
    db = get_db()
    academic_year_id = request.form['academic_year_id']

    for day_num in range(1, 8):
        status = request.form.get(f'status_{day_num}', 'nastavni')
        note = request.form.get(f'note_{day_num}', '').strip()

        existing = db.execute(
            'SELECT id FROM day_status WHERE academic_year_id = ? AND day_of_week = ?',
            (academic_year_id, day_num)
        ).fetchone()

        if existing:
            db.execute(
                'UPDATE day_status SET status = ?, note = ? WHERE id = ?',
                (status, note, existing['id'])
            )
        else:
            db.execute(
                'INSERT INTO day_status (academic_year_id, day_of_week, status, note) VALUES (?, ?, ?, ?)',
                (academic_year_id, day_num, status, note)
            )

    db.commit()
    flash('Status dana je spremljen.', 'success')
    return redirect(url_for('day_status.index', academic_year_id=academic_year_id))
