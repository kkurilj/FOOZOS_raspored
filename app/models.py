from datetime import datetime, timedelta
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

# Sva moguća vremena za start/end odabir
TIMES = [
    '08:00', '08:45', '09:30', '10:15', '11:00', '11:45',
    '12:30', '13:15', '14:00', '14:45', '15:30', '16:15',
    '17:00', '17:45', '18:30', '19:15', '20:00', '20:45',
]

WEEK_TYPES = ['kontinuirano', '1. tjedan', '2. tjedan']

GROUPS = ['A', 'B', 'C', 'D']

MODULES = ['A', 'B', 'C']

SEMESTER_TYPES = ['zimski', 'ljetni']

STUDY_MODES = ['redoviti', 'izvanredni']

DAYS_REDOVITI = {1: 'Ponedjeljak', 2: 'Utorak', 3: 'Srijeda', 4: 'Četvrtak', 5: 'Petak'}
DAYS_IZVANREDNI = {4: 'Četvrtak', 5: 'Petak', 6: 'Subota'}


def get_display_days(study_mode):
    """Vrati odgovarajući DAYS dict prema načinu studija."""
    if study_mode == 'izvanredni':
        return DAYS_IZVANREDNI
    return DAYS_REDOVITI


def get_week_dates(ref_date_str, study_mode):
    """Iz referentnog datuma izračunaj datume za dane u tjednu.

    Za izvanredne: vraća {4: 'dd.mm.yyyy.', 5: '...', 6: '...'}
    za čet-pet-sub tjedna u kojem je ref_date.
    """
    d = datetime.strptime(ref_date_str, '%Y-%m-%d')
    iso_day = d.isoweekday()  # 1=pon, 7=ned
    monday = d - timedelta(days=iso_day - 1)

    display_days = get_display_days(study_mode)
    day_dates = {}
    for day_num in display_days:
        day_date = monday + timedelta(days=day_num - 1)
        day_dates[day_num] = day_date.strftime('%d.%m.%Y.')
    return day_dates


def get_week_date_range(ref_date_str, study_mode):
    """Iz referentnog datuma izračunaj date_from i date_to za filtriranje.

    Za izvanredne: vraća (YYYY-MM-DD četvrtak, YYYY-MM-DD subota) tog tjedna.
    """
    d = datetime.strptime(ref_date_str, '%Y-%m-%d')
    iso_day = d.isoweekday()
    monday = d - timedelta(days=iso_day - 1)

    display_days = get_display_days(study_mode)
    day_nums = sorted(display_days.keys())
    date_from = (monday + timedelta(days=day_nums[0] - 1)).strftime('%Y-%m-%d')
    date_to = (monday + timedelta(days=day_nums[-1] - 1)).strftime('%Y-%m-%d')
    return date_from, date_to

PROFESSOR_TITLES = [
    '', 'mag.', 'dr.sc.', 'doc.dr.sc.', 'izv.prof.dr.sc.',
    'prof.dr.sc.', 'mr.sc.', 'v.pred.', 'pred.', 'asist.',
    'v.asist.', 'poslijedoktorand',
]

def _hsl_to_hex(h, s, l):
    """Pretvori HSL (h:0-360, s:0-1, l:0-1) u hex string."""
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l, s)
    return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))


def _generate_professor_colors(n=200):
    """Generiraj n razlicitih boja za profesore koristeci HSL."""
    colors = []
    sat_levels = [0.30, 0.50, 0.40, 0.60]
    light_bg = [0.88, 0.92, 0.85, 0.90]
    for i in range(n):
        hue = (i * 137.508) % 360  # zlatni kut za distribuciju
        variant = i % len(sat_levels)
        colors.append({
            'bg': _hsl_to_hex(hue, sat_levels[variant], light_bg[variant]),
            'border': _hsl_to_hex(hue, 0.70, 0.40),
            'text': _hsl_to_hex(hue, 0.60, 0.20),
        })
    return colors


PROFESSOR_COLORS = _generate_professor_colors(200)


def build_professor_colors(entries):
    """Izgradi mapiranje professor_id -> boja iz palete."""
    professor_ids = []
    seen = set()
    for entry in entries:
        pid = entry['professor_id']
        if pid not in seen:
            seen.add(pid)
            professor_ids.append(pid)
    return {pid: PROFESSOR_COLORS[i % len(PROFESSOR_COLORS)]
            for i, pid in enumerate(professor_ids)}


def date_to_day_of_week(date_str):
    """Pretvori datum (YYYY-MM-DD) u dan u tjednu (1=pon, 7=ned)."""
    d = datetime.strptime(date_str, '%Y-%m-%d')
    # isoweekday(): Monday=1, Sunday=7
    return d.isoweekday()


def times_overlap(start_a, end_a, start_b, end_b):
    """Provjeri preklapaju li se dva vremenska raspona."""
    return start_a < end_b and end_a > start_b


def weeks_overlap(week_type_a, week_type_b):
    """Provjeri da li se dva tipa tjedna preklapaju."""
    if week_type_a == 'kontinuirano' or week_type_b == 'kontinuirano':
        return True
    return week_type_a == week_type_b


def check_conflicts(entry_data, exclude_id=None):
    """Provjeri konflikte za novi/editirani unos rasporeda."""
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
        AND se.start_time < ?
        AND se.end_time > ?
    '''
    params = [
        entry_data['academic_year_id'],
        entry_data['day_of_week'],
        entry_data['end_time'],
        entry_data['start_time'],
    ]

    if exclude_id:
        query += ' AND se.id != ?'
        params.append(exclude_id)

    overlapping = db.execute(query, params).fetchall()

    for existing in overlapping:
        if not weeks_overlap(entry_data['week_type'], existing['week_type']):
            continue

        week_info = f" ({existing['week_type']})" if existing['week_type'] != 'kontinuirano' else ''
        time_info = f"{existing['start_time']}-{existing['end_time']}"

        if existing['professor_id'] == int(entry_data['professor_id']):
            prof_name = f"{existing['title']} {existing['first_name']} {existing['last_name']}".strip()
            conflicts.append(
                f"Profesor {prof_name} je već zauzet/a: "
                f"{existing['course_name']} u {existing['classroom_name']} ({time_info}){week_info}"
            )

        if existing['classroom_id'] == int(entry_data['classroom_id']):
            conflicts.append(
                f"Učionica {existing['classroom_name']} je već zauzeta: "
                f"{existing['course_name']} ({time_info}){week_info}"
            )

        if (existing['study_program_id'] == int(entry_data['study_program_id'])
                and existing['semester_number'] == int(entry_data['semester_number'])
                and existing['group_name'] == entry_data['group_name']
                and existing['study_mode'] == entry_data.get('study_mode', 'redoviti')):
            conflicts.append(
                f"Grupa {entry_data['group_name']} ({existing['program_name']}, "
                f"{existing['semester_number']}. semestar) već ima predavanje: "
                f"{existing['course_name']} ({time_info}){week_info}"
            )

    return conflicts


def build_timetable_grid(entries, days=None):
    """Izgradi grid strukturu za prikaz rasporeda.

    Stavka se prikazuje u svakom time slotu koji pokriva.
    days: dict {day_num: day_name} - koji dani se prikazuju (default: svi 1-7)
    Returns dict: {time_slot: {day_of_week: [entries]}}
    """
    if days is None:
        days = DAYS
    grid = {}
    for ts in TIME_SLOTS:
        grid[ts] = {}
        for day in days:
            grid[ts][day] = []

    for entry in entries:
        day = entry['day_of_week']
        if day not in days:
            continue
        e_start = entry['start_time']
        e_end = entry['end_time']

        for ts in TIME_SLOTS:
            slot_start, slot_end = ts.split(' - ')
            if e_start < slot_end and e_end > slot_start:
                grid[ts][day].append(entry)

    return grid


def build_day_dates(entries):
    """Izgradi mapiranje dan -> sortirani datumi (dd.mm.yyyy.) iz stavki.

    Automatski popunjava datume za sve dane u tjednu na temelju
    datuma iz stavki rasporeda.
    """
    day_dates = {}
    unique_dates = set()
    for entry in entries:
        unique_dates.add(entry['date'])

    for date_str in unique_dates:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        iso_day = d.isoweekday()  # 1=pon, 7=ned
        monday = d - timedelta(days=iso_day - 1)
        for day_num in range(1, 8):
            day_date = monday + timedelta(days=day_num - 1)
            if day_num not in day_dates:
                day_dates[day_num] = set()
            day_dates[day_num].add(day_date.strftime('%d.%m.%Y.'))

    return {day: sorted(dates) for day, dates in day_dates.items()}


def build_cell_info(grid, time_slots, days):
    """Izgradi info za renderiranje celija s rowspan spajanjem.

    Returns dict: {time_slot: {day: {'skip': bool, 'rowspan': int, 'entries': list}}}
    skip=True znaci da je celija pokrivena rowspanom odozgo.
    """
    ts_list = list(time_slots)
    slot_bounds = []
    for ts in ts_list:
        s, e = ts.split(' - ')
        slot_bounds.append((s, e))

    cell_info = {}
    for ts in ts_list:
        cell_info[ts] = {}
        for day in days:
            cell_info[ts][day] = {'skip': False, 'rowspan': 1, 'entries': []}

    for day in days:
        covered_until = 0
        parent_idx = 0

        for idx, ts in enumerate(ts_list):
            if idx < covered_until:
                cell_info[ts][day]['skip'] = True
                # Ako entry pocinje u pokrivenom slotu (druga grupa), dodaj u roditeljsku celiju
                slot_start = slot_bounds[idx][0]
                for entry in grid[ts][day]:
                    if entry['start_time'] == slot_start:
                        parent_ts = ts_list[parent_idx]
                        if not any(e['id'] == entry['id'] for e in cell_info[parent_ts][day]['entries']):
                            cell_info[parent_ts][day]['entries'].append(entry)
                continue

            slot_start = slot_bounds[idx][0]
            starting_entries = [e for e in grid[ts][day] if e['start_time'] == slot_start]

            if not starting_entries:
                cell_info[ts][day] = {'skip': False, 'rowspan': 1, 'entries': []}
                continue

            # Izracunaj rowspan = max span svih entry-ja koji pocinju ovdje
            max_span = 1
            for entry in starting_entries:
                span = 0
                for j in range(idx, len(ts_list)):
                    js, je = slot_bounds[j]
                    if entry['start_time'] < je and entry['end_time'] > js:
                        span += 1
                    else:
                        break
                max_span = max(max_span, span)

            cell_info[ts][day] = {
                'skip': False,
                'rowspan': max_span,
                'entries': list(starting_entries),
            }

            parent_idx = idx
            covered_until = idx + max_span

            # Pokupi entry-je koji pocinju u pokrivenim slotovima
            for k in range(idx + 1, min(covered_until, len(ts_list))):
                k_slot_start = slot_bounds[k][0]
                for entry in grid[ts_list[k]][day]:
                    if entry['start_time'] == k_slot_start:
                        if not any(e['id'] == entry['id'] for e in cell_info[ts][day]['entries']):
                            cell_info[ts][day]['entries'].append(entry)

    return cell_info


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
    if filters.get('study_mode'):
        query += ' AND se.study_mode = ?'
        params.append(filters['study_mode'])
    if filters.get('date_from') and filters.get('date_to'):
        query += ' AND se.date >= ? AND se.date <= ?'
        params.append(filters['date_from'])
        params.append(filters['date_to'])

    query += ' ORDER BY se.day_of_week, se.start_time'
    return db.execute(query, params).fetchall()
