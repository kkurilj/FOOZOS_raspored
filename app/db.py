import sqlite3
import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
        g.db.execute('PRAGMA journal_mode = WAL')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    """Inicijaliziraj bazu podataka."""
    init_db()
    click.echo('Baza podataka je inicijalizirana.')


def migrate_db(db):
    """Pokreni migracije za postojeću bazu."""
    # Provjeri postoji li study_mode stupac
    columns = [row[1] for row in db.execute('PRAGMA table_info(schedule_entry)').fetchall()]
    if 'study_mode' not in columns:
        db.execute("ALTER TABLE schedule_entry ADD COLUMN study_mode TEXT NOT NULL DEFAULT 'redoviti' CHECK (study_mode IN ('redoviti', 'izvanredni'))")
        db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
