from flask import Blueprint, render_template, redirect, url_for
from app.db import get_db
from app.auth import is_admin as check_admin, login_required

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    if not check_admin():
        return redirect(url_for('timetable.by_program'))
    db = get_db()
    stats = {
        'academic_years': db.execute('SELECT COUNT(*) FROM academic_year').fetchone()[0],
        'study_programs': db.execute('SELECT COUNT(*) FROM study_program').fetchone()[0],
        'professors': db.execute('SELECT COUNT(*) FROM professor').fetchone()[0],
        'classrooms': db.execute('SELECT COUNT(*) FROM classroom').fetchone()[0],
        'courses': db.execute('SELECT COUNT(*) FROM course').fetchone()[0],
        'schedule_entries': db.execute('SELECT COUNT(*) FROM schedule_entry').fetchone()[0],
    }
    return render_template('index.html', stats=stats)


@bp.route('/upute')
@login_required
def guide():
    return render_template('guide.html')
