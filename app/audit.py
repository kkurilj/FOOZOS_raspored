from flask import session
from app.db import get_db


def log_audit(action, entity_type, description, entity_id=None, db=None):
    """Zapiši akciju u audit_log i obriši zapise starije od 15 dana."""
    if db is None:
        db = get_db()
    db.execute('''
        INSERT INTO audit_log (user_id, user_name, action, entity_type, entity_id, description)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        session.get('user_id'),
        session.get('user_display_name', 'Nepoznat'),
        action,
        entity_type,
        entity_id,
        description,
    ))
    db.execute("DELETE FROM audit_log WHERE created_at < datetime('now', 'localtime', '-15 days')")
