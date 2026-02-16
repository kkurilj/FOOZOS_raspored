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
    se_columns = [row[1] for row in db.execute('PRAGMA table_info(schedule_entry)').fetchall()]

    # Stara migracija: dodaj study_mode u schedule_entry (za stare baze)
    if 'study_mode' not in se_columns:
        db.execute("ALTER TABLE schedule_entry ADD COLUMN study_mode TEXT NOT NULL DEFAULT 'redoviti' CHECK (study_mode IN ('redoviti', 'izvanredni'))")
        db.commit()
        se_columns.append('study_mode')

    # Migracija: dozvoli NULL za group_name (recreate tablice)
    col_info = db.execute('PRAGMA table_info(schedule_entry)').fetchall()
    group_col = [c for c in col_info if c[1] == 'group_name']
    if group_col and group_col[0][3]:  # notnull == 1
        db.executescript('''
            CREATE TABLE schedule_entry_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                academic_year_id INTEGER NOT NULL,
                study_program_id INTEGER NOT NULL,
                semester_type TEXT NOT NULL CHECK (semester_type IN ('zimski', 'ljetni')),
                semester_number INTEGER NOT NULL CHECK (semester_number BETWEEN 1 AND 10),
                course_id INTEGER NOT NULL,
                group_name TEXT CHECK (group_name IN (NULL, 'A', 'B', 'C', 'D')),
                module_name TEXT CHECK (module_name IN (NULL, 'A', 'B', 'C')),
                professor_id INTEGER NOT NULL,
                classroom_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                week_type TEXT NOT NULL CHECK (week_type IN ('kontinuirano', '1. tjedan', '2. tjedan')),
                study_mode TEXT NOT NULL DEFAULT 'redoviti' CHECK (study_mode IN ('redoviti', 'izvanredni')),
                FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE,
                FOREIGN KEY (study_program_id) REFERENCES study_program(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
                FOREIGN KEY (professor_id) REFERENCES professor(id) ON DELETE CASCADE,
                FOREIGN KEY (classroom_id) REFERENCES classroom(id) ON DELETE CASCADE
            );
            INSERT INTO schedule_entry_new SELECT * FROM schedule_entry;
            DROP TABLE schedule_entry;
            ALTER TABLE schedule_entry_new RENAME TO schedule_entry;
            CREATE INDEX idx_schedule_day_time ON schedule_entry(day_of_week, start_time);
            CREATE INDEX idx_schedule_date ON schedule_entry(date);
            CREATE INDEX idx_schedule_professor ON schedule_entry(professor_id);
            CREATE INDEX idx_schedule_classroom ON schedule_entry(classroom_id);
            CREATE INDEX idx_schedule_program_semester ON schedule_entry(study_program_id, semester_number);
        ''')

    # Migracija: premjesti study_mode iz schedule_entry u study_program
    sp_columns = [row[1] for row in db.execute('PRAGMA table_info(study_program)').fetchall()]
    se_columns = [row[1] for row in db.execute('PRAGMA table_info(schedule_entry)').fetchall()]

    if 'study_mode' not in sp_columns:
        db.execute("ALTER TABLE study_program ADD COLUMN study_mode TEXT NOT NULL DEFAULT 'redoviti' CHECK (study_mode IN ('redoviti', 'izvanredni'))")
        # Kopiraj study_mode iz schedule_entry u study_program (najčešći mode po programu)
        if 'study_mode' in se_columns:
            rows = db.execute('''
                SELECT study_program_id, study_mode, COUNT(*) as cnt
                FROM schedule_entry
                GROUP BY study_program_id, study_mode
                ORDER BY study_program_id, cnt DESC
            ''').fetchall()
            seen = set()
            for row in rows:
                sp_id = row[0]
                if sp_id not in seen:
                    seen.add(sp_id)
                    db.execute('UPDATE study_program SET study_mode = ? WHERE id = ?', (row[1], sp_id))
        db.commit()

    if 'study_mode' in se_columns:
        db.executescript('''
            CREATE TABLE schedule_entry_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                academic_year_id INTEGER NOT NULL,
                study_program_id INTEGER NOT NULL,
                semester_type TEXT NOT NULL CHECK (semester_type IN ('zimski', 'ljetni')),
                semester_number INTEGER NOT NULL CHECK (semester_number BETWEEN 1 AND 10),
                course_id INTEGER NOT NULL,
                group_name TEXT CHECK (group_name IN (NULL, 'A', 'B', 'C', 'D')),
                module_name TEXT CHECK (module_name IN (NULL, 'A', 'B', 'C')),
                professor_id INTEGER NOT NULL,
                classroom_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                week_type TEXT NOT NULL CHECK (week_type IN ('kontinuirano', '1. tjedan', '2. tjedan')),
                FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE,
                FOREIGN KEY (study_program_id) REFERENCES study_program(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
                FOREIGN KEY (professor_id) REFERENCES professor(id) ON DELETE CASCADE,
                FOREIGN KEY (classroom_id) REFERENCES classroom(id) ON DELETE CASCADE
            );
            INSERT INTO schedule_entry_new
                (id, academic_year_id, study_program_id, semester_type, semester_number,
                 course_id, group_name, module_name, professor_id, classroom_id,
                 date, day_of_week, start_time, end_time, week_type)
            SELECT id, academic_year_id, study_program_id, semester_type, semester_number,
                   course_id, group_name, module_name, professor_id, classroom_id,
                   date, day_of_week, start_time, end_time, week_type
            FROM schedule_entry;
            DROP TABLE schedule_entry;
            ALTER TABLE schedule_entry_new RENAME TO schedule_entry;
            CREATE INDEX idx_schedule_day_time ON schedule_entry(day_of_week, start_time);
            CREATE INDEX idx_schedule_date ON schedule_entry(date);
            CREATE INDEX idx_schedule_professor ON schedule_entry(professor_id);
            CREATE INDEX idx_schedule_classroom ON schedule_entry(classroom_id);
            CREATE INDEX idx_schedule_program_semester ON schedule_entry(study_program_id, semester_number);
        ''')


    # Migracija: dodati teaching_form u schedule_entry
    se_columns = [row[1] for row in db.execute('PRAGMA table_info(schedule_entry)').fetchall()]
    if 'teaching_form' not in se_columns:
        db.execute("ALTER TABLE schedule_entry ADD COLUMN teaching_form TEXT NOT NULL DEFAULT 'predavanja'")
        db.commit()

    # Migracija: dodati element u study_program
    sp_columns = [row[1] for row in db.execute('PRAGMA table_info(study_program)').fetchall()]
    if 'element' not in sp_columns:
        db.execute("ALTER TABLE study_program ADD COLUMN element TEXT NOT NULL DEFAULT ''")
        db.commit()

    # Migracija: dodati study_program_id u course
    course_columns = [row[1] for row in db.execute('PRAGMA table_info(course)').fetchall()]
    if 'study_program_id' not in course_columns:
        db.execute("ALTER TABLE course ADD COLUMN study_program_id INTEGER REFERENCES study_program(id)")
        db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
