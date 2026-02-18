from flask import Blueprint, render_template
from app.db import get_db
from app.auth import super_admin_required

bp = Blueprint('audit_log', __name__)

ENTITY_LABELS = {
    'academic_year': 'Akademska godina',
    'study_program': 'Studijski program',
    'professor': 'Profesor',
    'classroom': 'Učionica',
    'course': 'Kolegij',
    'schedule_entry': 'Stavka rasporeda',
    'user': 'Korisnik',
    'day_status': 'Status dana',
    'database': 'Baza podataka',
}

ACTION_LABELS = {
    'create': ('Kreiranje', 'bg-success', 'bi-plus-circle'),
    'update': ('Uređivanje', 'bg-primary', 'bi-pencil'),
    'delete': ('Brisanje', 'bg-danger', 'bi-trash'),
    'import': ('Uvoz', 'bg-info', 'bi-upload'),
    'export': ('Izvoz', 'bg-secondary', 'bi-download'),
    'undo': ('Poništavanje', 'bg-warning text-dark', 'bi-arrow-counterclockwise'),
}


@bp.route('/')
@super_admin_required
def index():
    db = get_db()
    logs = db.execute('''
        SELECT * FROM audit_log
        WHERE created_at >= datetime('now', 'localtime', '-15 days')
        ORDER BY id DESC
    ''').fetchall()
    return render_template(
        'audit_log/index.html',
        logs=logs,
        entity_labels=ENTITY_LABELS,
        action_labels=ACTION_LABELS,
    )
