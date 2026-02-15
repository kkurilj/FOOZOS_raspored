from app.db import get_db

DAYS = {
    1: 'Ponedjeljak',
    2: 'Utorak',
    3: 'Srijeda',
    4: 'Četvrtak',
    5: 'Petak',
    6: 'Subota',
    7: 'Nedjelja',
}

DAY_STATUSES = ['neradni', 'praznik', 'nenastavni']

TIME_SLOTS = [
    '08:00 - 08:45',
    '08:45 - 09:30',
    '09:30 - 10:15',
    '10:15 - 11:00',
    '11:00 - 11:45',
    '11:45 - 12:30',
    '12:30 - 13:15',
    '13:15 - 14:00',
    '14:00 - 14:45',
    '14:45 - 15:30',
    '15:30 - 16:15',
    '16:15 - 17:00',
    '17:00 - 17:45',
    '17:45 - 18:30',
    '18:30 - 19:15',
    '19:15 - 20:00',
    '20:00 - 20:45',
]

WEEK_TYPES = ['kontinuirano', '1. tjedan', '2. tjedan']

GROUPS = ['A', 'B', 'C', 'D']

MODULES = ['A', 'B', 'C']

SEMESTER_TYPES = ['zimski', 'ljetni']

PROFESSOR_TITLES = [
    '', 'mag.', 'dr.sc.', 'doc.dr.sc.', 'izv.prof.dr.sc.',
    'prof.dr.sc.', 'mr.sc.', 'v.pred.', 'pred.', 'asist.',
    'v.asist.', 'poslijedoktorand',
]


def weeks_overlap(week_type_a, week_type_b):
    """Provjeri da li se dva tipa tjedna preklapaju."""
    if week_type_a == 'kontinuirano' or week_type_b == 'kontinuirano':
        return True
    return week_type_a == week_type_b


def check_conflicts(entry_data, exclude_id=None):
    """Provjeri konflikte za novi/editirani unos rasporeda.

    Returns lista konflikata kao stringova. Prazna lista = nema konflikata.
    """
    db = get_db()
    conflicts = []

    query = '''
        SELECT se.*, c.name as course_name, p.first_name, p.last_name, p.title,
               cl.name as classroom_name, sp.name as program_name
        FROM schedule_entry se
        JOIN course c ON se.course_id = c.id
        JOIN professor p ON se.professor_id = p.id
        JOIN classroom cl ON se.classroom_id = cl.id
        JOIN study_program sp ON se.study_program_id = sp.id
        WHERE se.academic_year_id = ?
        AND se.day_of_week = ?
        AND se.time_slot = ?
    '''
    params = [
        entry_data['academic_year_id'],
        entry_data['day_of_week'],
        entry_data['time_slot'],
    ]

    if exclude_id:
        query += ' AND se.id != ?'
        params.append(exclude_id)

    overlapping = db.execute(query, params).fetchall()

    for existing in overlapping:
        if not weeks_overlap(entry_data['week_type'], existing['week_type']):
            continue

        week_info = f" ({existing['week_type']})" if existing['week_type'] != 'kontinuirano' else ''

        if existing['professor_id'] == int(entry_data['professor_id']):
            prof_name = f"{existing['title']} {existing['first_name']} {existing['last_name']}".strip()
            conflicts.append(
                f"Profesor {prof_name} je već zauzet/a: "
                f"{existing['course_name']} u {existing['classroom_name']}{week_info}"
            )

        if existing['classroom_id'] == int(entry_data['classroom_id']):
            conflicts.append(
                f"Učionica {existing['classroom_name']} je već zauzeta: "
                f"{existing['course_name']} ({existing['title']} {existing['first_name']} {existing['last_name']}){week_info}".strip()
            )

        if (existing['study_program_id'] == int(entry_data['study_program_id'])
                and existing['semester_number'] == int(entry_data['semester_number'])
                and existing['group_name'] == entry_data['group_name']):
            conflicts.append(
                f"Grupa {entry_data['group_name']} ({existing['program_name']}, "
                f"{existing['semester_number']}. semestar) već ima predavanje: "
                f"{existing['course_name']}{week_info}"
            )

    return conflicts


def build_timetable_grid(entries):
    """Izgradi grid strukturu za prikaz rasporeda.

    Returns dict: {time_slot: {day_of_week: [entries]}}
    """
    grid = {}
    for ts in TIME_SLOTS:
        grid[ts] = {}
        for day in range(1, 8):
            grid[ts][day] = []

    for entry in entries:
        ts = entry['time_slot']
        day = entry['day_of_week']
        if ts in grid and day in grid[ts]:
            grid[ts][day].append(entry)

    return grid


def get_schedule_entries(filters):
    """Dohvati stavke rasporeda s filterima."""
    db = get_db()

    query = '''
        SELECT se.*, c.name as course_name, c.code as course_code,
               p.first_name, p.last_name, p.title,
               cl.name as classroom_name,
               sp.name as program_name, sp.code as program_code,
               ay.name as academic_year_name
        FROM schedule_entry se
        JOIN course c ON se.course_id = c.id
        JOIN professor p ON se.professor_id = p.id
        JOIN classroom cl ON se.classroom_id = cl.id
        JOIN study_program sp ON se.study_program_id = sp.id
        JOIN academic_year ay ON se.academic_year_id = ay.id
        WHERE 1=1
    '''
    params = []

    if filters.get('academic_year_id'):
        query += ' AND se.academic_year_id = ?'
        params.append(filters['academic_year_id'])
    if filters.get('study_program_id'):
        query += ' AND se.study_program_id = ?'
        params.append(filters['study_program_id'])
    if filters.get('semester_type'):
        query += ' AND se.semester_type = ?'
        params.append(filters['semester_type'])
    if filters.get('semester_number'):
        query += ' AND se.semester_number = ?'
        params.append(filters['semester_number'])
    if filters.get('professor_id'):
        query += ' AND se.professor_id = ?'
        params.append(filters['professor_id'])
    if filters.get('classroom_id'):
        query += ' AND se.classroom_id = ?'
        params.append(filters['classroom_id'])
    if filters.get('week_type'):
        if filters['week_type'] == 'kontinuirano':
            query += " AND se.week_type = 'kontinuirano'"
        elif filters['week_type'] == '1. tjedan':
            query += " AND se.week_type IN ('kontinuirano', '1. tjedan')"
        elif filters['week_type'] == '2. tjedan':
            query += " AND se.week_type IN ('kontinuirano', '2. tjedan')"

    query += ' ORDER BY se.day_of_week, se.time_slot'
    return db.execute(query, params).fetchall()
