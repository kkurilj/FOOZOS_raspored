from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from app.db import get_db
from app.auth import is_admin as check_admin, login_required
from app.audit import log_audit

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
        'unpublished': db.execute('SELECT COUNT(*) FROM schedule_entry WHERE is_published = 0').fetchone()[0],
        'conflicts': db.execute('SELECT COUNT(*) FROM schedule_entry WHERE has_conflict = 1').fetchone()[0],
    }
    return render_template('index.html', stats=stats)


@bp.route('/publish', methods=['POST'])
@login_required
def publish():
    db = get_db()
    count = db.execute('SELECT COUNT(*) FROM schedule_entry WHERE is_published = 0').fetchone()[0]
    if count > 0:
        db.execute('UPDATE schedule_entry SET is_published = 1 WHERE is_published = 0')
        log_audit('publish', 'schedule_entry', f'Objavljeno {count} stavki rasporeda')
        db.commit()
        flash(f'Uspješno objavljeno {count} stavki rasporeda.', 'success')
    else:
        flash('Nema neobjavljenih stavki.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/upute')
@login_required
def guide():
    return render_template('guide.html')


@bp.route('/health')
def health():
    """Health check endpoint za monitoring."""
    try:
        db = get_db()
        db.execute('SELECT 1').fetchone()
        return jsonify({'status': 'ok'}), 200
    except Exception:
        return jsonify({'status': 'error'}), 503
