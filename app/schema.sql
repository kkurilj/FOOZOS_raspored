DROP TABLE IF EXISTS day_status;
DROP TABLE IF EXISTS schedule_entry;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS professor;
DROP TABLE IF EXISTS classroom;
DROP TABLE IF EXISTS study_program;
DROP TABLE IF EXISTS academic_year;

CREATE TABLE academic_year (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    is_default INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE study_program (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    study_mode TEXT NOT NULL DEFAULT 'redoviti' CHECK (study_mode IN ('redoviti', 'izvanredni')),
    element TEXT NOT NULL DEFAULT '',
    UNIQUE(code, element)
);

CREATE TABLE professor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    UNIQUE(first_name, last_name)
);

CREATE TABLE classroom (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    study_program_id INTEGER,
    FOREIGN KEY (study_program_id) REFERENCES study_program(id) ON DELETE CASCADE,
    UNIQUE(code, study_program_id)
);

CREATE TABLE schedule_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    academic_year_id INTEGER NOT NULL,
    study_program_id INTEGER NOT NULL,
    semester_type TEXT NOT NULL CHECK (semester_type IN ('zimski', 'ljetni')),
    semester_number INTEGER NOT NULL CHECK (semester_number BETWEEN 1 AND 10),
    course_id INTEGER NOT NULL,
    group_name TEXT CHECK (group_name IN (NULL, 'A', 'B', 'C', 'D')),
    module_name TEXT CHECK (module_name IN (NULL, 'A', 'B', 'C')),
    teaching_form TEXT NOT NULL DEFAULT 'predavanja' CHECK (teaching_form IN ('predavanja', 'seminari', 'vježbe')),
    professor_id INTEGER NOT NULL,
    classroom_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    week_type TEXT NOT NULL CHECK (week_type IN ('kontinuirano', '1. tjedan', '2. tjedan')),
    has_conflict INTEGER NOT NULL DEFAULT 0,
    is_published INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE,
    FOREIGN KEY (study_program_id) REFERENCES study_program(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    FOREIGN KEY (professor_id) REFERENCES professor(id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(id) ON DELETE CASCADE
);

CREATE INDEX idx_schedule_day_time ON schedule_entry(day_of_week, start_time);
CREATE INDEX idx_schedule_date ON schedule_entry(date);
CREATE INDEX idx_schedule_professor ON schedule_entry(professor_id);
CREATE INDEX idx_schedule_classroom ON schedule_entry(classroom_id);
CREATE INDEX idx_schedule_program_semester ON schedule_entry(study_program_id, semester_number);

CREATE TABLE schedule_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('create', 'update', 'delete', 'move')),
    old_data TEXT,
    new_data TEXT,
    user_id INTEGER,
    user_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL DEFAULT '',
    last_name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('super_admin', 'admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE login_attempt (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    attempted_at REAL NOT NULL
);
CREATE INDEX idx_login_attempt_ip ON login_attempt(ip_address, attempted_at);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_name TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);

CREATE TABLE day_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    academic_year_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    status TEXT NOT NULL CHECK (status IN ('neradni', 'praznik', 'nenastavni')),
    note TEXT DEFAULT '',
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE,
    UNIQUE(academic_year_id, day_of_week)
);
