DROP TABLE IF EXISTS day_status;
DROP TABLE IF EXISTS schedule_entry;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS professor;
DROP TABLE IF EXISTS classroom;
DROP TABLE IF EXISTS study_program;
DROP TABLE IF EXISTS academic_year;

CREATE TABLE academic_year (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE study_program (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE
);

CREATE TABLE professor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT ''
);

CREATE TABLE classroom (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE
);

CREATE TABLE schedule_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    academic_year_id INTEGER NOT NULL,
    study_program_id INTEGER NOT NULL,
    semester_type TEXT NOT NULL CHECK (semester_type IN ('zimski', 'ljetni')),
    semester_number INTEGER NOT NULL CHECK (semester_number BETWEEN 1 AND 10),
    course_id INTEGER NOT NULL,
    group_name TEXT NOT NULL CHECK (group_name IN ('A', 'B', 'C', 'D')),
    module_name TEXT CHECK (module_name IN (NULL, 'A', 'B', 'C')),
    professor_id INTEGER NOT NULL,
    classroom_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    time_slot TEXT NOT NULL,
    week_type TEXT NOT NULL CHECK (week_type IN ('kontinuirano', '1. tjedan', '2. tjedan')),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE,
    FOREIGN KEY (study_program_id) REFERENCES study_program(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE,
    FOREIGN KEY (professor_id) REFERENCES professor(id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classroom(id) ON DELETE CASCADE
);

CREATE INDEX idx_schedule_day_time ON schedule_entry(day_of_week, time_slot);
CREATE INDEX idx_schedule_professor ON schedule_entry(professor_id);
CREATE INDEX idx_schedule_classroom ON schedule_entry(classroom_id);
CREATE INDEX idx_schedule_program_semester ON schedule_entry(study_program_id, semester_number);

CREATE TABLE day_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    academic_year_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    status TEXT NOT NULL CHECK (status IN ('nastavni', 'neradni', 'praznik', 'nenastavni')) DEFAULT 'nastavni',
    note TEXT DEFAULT '',
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(id) ON DELETE CASCADE,
    UNIQUE(academic_year_id, day_of_week)
);
