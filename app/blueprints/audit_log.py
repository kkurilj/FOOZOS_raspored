import csv
import io
from flask import Blueprint, render_template, make_response
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
    'auth': 'Prijava',
}

ACTION_LABELS = {
    'create': ('Kreiranje', 'bg-success', 'bi-plus-circle'),
    'update': ('Uređivanje', 'bg-primary', 'bi-pencil'),
    'delete': ('Brisanje', 'bg-danger', 'bi-trash'),
    'import': ('Uvoz', 'bg-info', 'bi-upload'),
    'export': ('Izvoz', 'bg-secondary', 'bi-download'),
    'undo': ('Poništavanje', 'bg-warning text-dark', 'bi-arrow-counterclockwise'),
    'login': ('Prijava', 'bg-success', 'bi-box-arrow-in-right'),
    'login_failed': ('Neuspjela prijava', 'bg-danger', 'bi-shield-exclamation'),
    'logout': ('Odjava', 'bg-secondary', 'bi-box-arrow-right'),
    'publish': ('Objava', 'bg-info', 'bi-megaphone'),
    'copy': ('Kopiranje', 'bg-primary', 'bi-copy'),
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


@bp.route('/export')
@super_admin_required
def export_csv():
    db = get_db()
    logs = db.execute('''
        SELECT * FROM audit_log
        WHERE created_at >= datetime('now', 'localtime', '-15 days')
        ORDER BY id DESC
    ''').fetchall()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Datum i vrijeme', 'Akcija', 'Vrsta', 'Opis', 'Korisnik'])
    for log in logs:
        action_label = ACTION_LABELS.get(log['action'], (log['action'],))[0]
        entity_label = ENTITY_LABELS.get(log['entity_type'], log['entity_type'])
        writer.writerow([
            log['created_at'],
            action_label,
            entity_label,
            log['description'],
            log['user_name'],
        ])

    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
    resp.headers['Content-Disposition'] = 'attachment; filename=evidencija_promjena.csv'
    return resp
