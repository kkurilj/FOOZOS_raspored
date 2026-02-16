import io
from datetime import date
from flask import Blueprint, render_template, request, make_response, send_file
from app.db import get_db
from app.models import (
    DAYS, TIME_SLOTS, WEEK_TYPES, SEMESTER_TYPES, STUDY_MODES,
    get_schedule_entries, build_timetable_grid, compute_day_columns, build_cell_info,
    build_professor_colors, build_day_dates, get_display_days, get_week_dates, get_week_date_range
)

bp = Blueprint('timetable', __name__)


def get_day_statuses(academic_year_id):
    """Load day statuses for an academic year as {day_of_week: {status, note}}."""
    if not academic_year_id:
        return {}
    db = get_db()
    rows = db.execute(
        'SELECT day_of_week, status, note FROM day_status WHERE academic_year_id = ?',
        (academic_year_id,)
    ).fetchall()
    return {r['day_of_week']: {'status': r['status'], 'note': r['note']} for r in rows}


def get_filter_options():
    db = get_db()
    return {
        'academic_years': db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall(),
        'study_programs': db.execute('SELECT * FROM study_program ORDER BY name').fetchall(),
        'professors': db.execute('SELECT * FROM professor ORDER BY last_name, first_name').fetchall(),
        'classrooms': db.execute('SELECT * FROM classroom ORDER BY name').fetchall(),
        'week_types': WEEK_TYPES,
        'semester_types': SEMESTER_TYPES,
        'study_modes': STUDY_MODES,
        'days': DAYS,
        'time_slots': TIME_SLOTS,
    }


def _apply_study_mode_context(filters):
    """Izračunaj display_days i day_dates iz study_mode i schedule_date filtera."""
    study_mode = filters.get('study_mode')
    schedule_date = filters.get('schedule_date')
    display_days = get_display_days(study_mode)
    day_dates = {}

    if study_mode == 'izvanredni':
        if not schedule_date:
            schedule_date = date.today().strftime('%Y-%m-%d')
            filters['schedule_date'] = schedule_date
        day_dates = get_week_dates(schedule_date, study_mode)
        date_from, date_to = get_week_date_range(schedule_date, study_mode)
        filters['date_from'] = date_from
        filters['date_to'] = date_to

    return display_days, day_dates


def _build_title_and_filters(view_type):
    """Build title and filters from request args based on view type."""
    filters = {}
    title = 'Raspored'
    db = get_db()

    if view_type == 'program':
        filters = {
            'academic_year_id': request.args.get('academic_year_id', type=int),
            'study_program_id': request.args.get('study_program_id', type=int),
            'semester_type': request.args.get('semester_type'),
            'semester_number': request.args.get('semester_number', type=int),
            'week_type': request.args.get('week_type'),
            'study_mode': request.args.get('study_mode'),
            'schedule_date': request.args.get('schedule_date'),
        }
        if filters.get('study_program_id'):
            prog = db.execute('SELECT * FROM study_program WHERE id = ?',
                              (filters['study_program_id'],)).fetchone()
            if prog:
                sem_num = filters.get('semester_number', '')
                sem_type = filters.get('semester_type', '')
                title = f"Raspored - {prog['name']} - {sem_num}. semestar ({sem_type})"
                if not filters.get('study_mode'):
                    filters['study_mode'] = prog['study_mode']

    elif view_type == 'classroom':
        filters = {
            'academic_year_id': request.args.get('academic_year_id', type=int),
            'classroom_id': request.args.get('classroom_id', type=int),
            'week_type': request.args.get('week_type'),
            'study_mode': request.args.get('study_mode'),
            'schedule_date': request.args.get('schedule_date'),
        }
        if filters.get('classroom_id'):
            room = db.execute('SELECT * FROM classroom WHERE id = ?',
                              (filters['classroom_id'],)).fetchone()
            if room:
                title = f"Raspored - Učionica {room['name']}"

    elif view_type == 'professor':
        filters = {
            'academic_year_id': request.args.get('academic_year_id', type=int),
            'professor_id': request.args.get('professor_id', type=int),
            'week_type': request.args.get('week_type'),
            'study_mode': request.args.get('study_mode'),
            'schedule_date': request.args.get('schedule_date'),
        }
        if filters.get('professor_id'):
            prof = db.execute('SELECT * FROM professor WHERE id = ?',
                              (filters['professor_id'],)).fetchone()
            if prof:
                title = f"Raspored - {prof['title']} {prof['first_name']} {prof['last_name']}".strip()

    if filters.get('study_mode') == 'izvanredni':
        title += ' - Izvanredni'

    if filters.get('academic_year_id'):
        ay = db.execute('SELECT * FROM academic_year WHERE id = ?',
                        (filters['academic_year_id'],)).fetchone()
        if ay:
            title += f" ({ay['name']})"

    return title, filters


@bp.route('/program')
def by_program():
    filters = {
        'academic_year_id': request.args.get('academic_year_id', type=int),
        'study_program_id': request.args.get('study_program_id', type=int),
        'semester_type': request.args.get('semester_type'),
        'semester_number': request.args.get('semester_number', type=int),
        'week_type': request.args.get('week_type'),
        'study_mode': request.args.get('study_mode'),
        'schedule_date': request.args.get('schedule_date'),
    }

    # Auto-detect study_mode iz odabranog programa
    if filters.get('study_program_id') and not filters.get('study_mode'):
        db = get_db()
        prog = db.execute(
            'SELECT study_mode FROM study_program WHERE id = ?',
            (filters['study_program_id'],)
        ).fetchone()
        if prog:
            filters['study_mode'] = prog['study_mode']

    display_days, day_dates = _apply_study_mode_context(filters)

    entries = get_schedule_entries(filters) if any(filters.values()) else []
    if not day_dates and entries:
        day_dates = build_day_dates(entries, display_days)
    day_cols, entry_tracks = compute_day_columns(entries, display_days)
    grid = build_timetable_grid(entries, display_days)
    cell_info = build_cell_info(grid, TIME_SLOTS, display_days, day_cols, entry_tracks)
    prof_colors = build_professor_colors(entries)

    day_statuses = get_day_statuses(filters.get('academic_year_id'))

    return render_template(
        'timetable/by_program.html',
        grid=grid, cell_info=cell_info, entries=entries, filters=filters,
        prof_colors=prof_colors, day_statuses=day_statuses, day_columns=day_cols,
        display_days=display_days, day_dates=day_dates,
        **get_filter_options()
    )


@bp.route('/classroom')
def by_classroom():
    filters = {
        'academic_year_id': request.args.get('academic_year_id', type=int),
        'classroom_id': request.args.get('classroom_id', type=int),
        'week_type': request.args.get('week_type'),
        'study_mode': request.args.get('study_mode'),
        'schedule_date': request.args.get('schedule_date'),
    }

    display_days, day_dates = _apply_study_mode_context(filters)

    entries = get_schedule_entries(filters) if (filters.get('classroom_id') or filters.get('academic_year_id')) else []
    if not day_dates and entries:
        day_dates = build_day_dates(entries, display_days)
    day_cols, entry_tracks = compute_day_columns(entries, display_days)
    grid = build_timetable_grid(entries, display_days)
    cell_info = build_cell_info(grid, TIME_SLOTS, display_days, day_cols, entry_tracks)
    prof_colors = build_professor_colors(entries)

    day_statuses = get_day_statuses(filters.get('academic_year_id'))

    # Per-classroom grids when showing all classrooms
    per_classroom = []
    if entries and not filters.get('classroom_id'):
        from collections import defaultdict
        grouped = defaultdict(list)
        for e in entries:
            grouped[e['classroom_id']].append(e)
        for cid in sorted(grouped, key=lambda c: grouped[c][0]['classroom_name']):
            c_entries = grouped[cid]
            c_day_cols, c_entry_tracks = compute_day_columns(c_entries, display_days)
            c_grid = build_timetable_grid(c_entries, display_days)
            c_cell_info = build_cell_info(c_grid, TIME_SLOTS, display_days, c_day_cols, c_entry_tracks)
            c_prof_colors = build_professor_colors(c_entries)
            per_classroom.append({
                'name': c_entries[0]['classroom_name'],
                'grid': c_grid,
                'cell_info': c_cell_info,
                'prof_colors': c_prof_colors,
                'day_columns': c_day_cols,
            })

    return render_template(
        'timetable/by_classroom.html',
        grid=grid, cell_info=cell_info, entries=entries, filters=filters,
        prof_colors=prof_colors, day_statuses=day_statuses, day_columns=day_cols,
        display_days=display_days, day_dates=day_dates,
        per_classroom=per_classroom,
        **get_filter_options()
    )


@bp.route('/professor')
def by_professor():
    filters = {
        'academic_year_id': request.args.get('academic_year_id', type=int),
        'professor_id': request.args.get('professor_id', type=int),
        'week_type': request.args.get('week_type'),
        'study_mode': request.args.get('study_mode'),
        'schedule_date': request.args.get('schedule_date'),
    }

    display_days, day_dates = _apply_study_mode_context(filters)

    entries = get_schedule_entries(filters) if filters.get('professor_id') else []
    if not day_dates and entries:
        day_dates = build_day_dates(entries, display_days)
    day_cols, entry_tracks = compute_day_columns(entries, display_days)
    grid = build_timetable_grid(entries, display_days)
    cell_info = build_cell_info(grid, TIME_SLOTS, display_days, day_cols, entry_tracks)
    prof_colors = build_professor_colors(entries)

    day_statuses = get_day_statuses(filters.get('academic_year_id'))

    return render_template(
        'timetable/by_professor.html',
        grid=grid, cell_info=cell_info, entries=entries, filters=filters,
        prof_colors=prof_colors, day_statuses=day_statuses, day_columns=day_cols,
        display_days=display_days, day_dates=day_dates,
        **get_filter_options()
    )


@bp.route('/pdf')
def export_pdf():
    view_type = request.args.get('view', 'program')
    title, filters = _build_title_and_filters(view_type)
    display_days, day_dates = _apply_study_mode_context(filters)

    entries = get_schedule_entries(filters) if any(filters.values()) else []
    if not day_dates and entries:
        day_dates = build_day_dates(entries, display_days)
    day_cols, entry_tracks = compute_day_columns(entries, display_days)
    grid = build_timetable_grid(entries, display_days)
    cell_info = build_cell_info(grid, TIME_SLOTS, display_days, day_cols, entry_tracks)
    prof_colors = build_professor_colors(entries)

    html = render_template(
        'pdf/timetable_pdf.html',
        grid=grid, cell_info=cell_info, title=title, view_type=view_type,
        days=display_days, time_slots=TIME_SLOTS,
        prof_colors=prof_colors, day_dates=day_dates, day_columns=day_cols
    )

    try:
        from weasyprint import HTML
        pdf = HTML(string=html).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename="raspored.pdf"'
        return response
    except ImportError:
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@bp.route('/excel')
def export_excel():
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    view_type = request.args.get('view', 'program')
    title, filters = _build_title_and_filters(view_type)
    display_days, day_dates = _apply_study_mode_context(filters)

    entries = get_schedule_entries(filters) if any(filters.values()) else []
    if not day_dates and entries:
        day_dates = build_day_dates(entries, display_days)
    day_cols, entry_tracks = compute_day_columns(entries, display_days)
    grid = build_timetable_grid(entries, display_days)
    ci = build_cell_info(grid, TIME_SLOTS, display_days, day_cols, entry_tracks)
    prof_colors = build_professor_colors(entries)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Raspored'

    # Styles
    header_font = Font(name='Arial', bold=True, color='FFFFFF', size=10)
    header_fill = PatternFill(start_color='2C5F8A', end_color='2C5F8A', fill_type='solid')
    time_fill = PatternFill(start_color='F0F2F5', end_color='F0F2F5', fill_type='solid')
    time_font = Font(name='Arial', bold=True, size=9)
    entry_font = Font(name='Arial', size=8)
    med_border = Border(
        left=Side(style='medium'), right=Side(style='medium'),
        top=Side(style='medium'), bottom=Side(style='medium')
    )
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

    def _format_entry(e):
        parts = [e['course_name'], f"{e['start_time']}-{e['end_time']}"]
        if view_type != 'professor':
            prof = f"{e['title']} {e['first_name']} {e['last_name']}".strip()
            parts.append(prof)
        if view_type != 'classroom':
            parts.append(e['classroom_name'])
        if view_type in ('classroom', 'professor'):
            parts.append(f"{e['program_name']} ({e['semester_number']}.sem)")
        if e['group_name']:
            parts.append(f"Grupa: {e['group_name']}")
        if e['module_name']:
            parts.append(f"Modul: {e['module_name']}")
        if e['week_type'] != 'kontinuirano':
            parts.append(f"[{e['week_type']}]")
        if e['study_mode'] == 'izvanredni':
            parts.append('[Izv.]')
        return '\n'.join(parts)

    # Mapiranje dan -> pocetni stupac u Excelu
    day_col_start = {}
    col_cursor = 2  # stupac 1 = Vrijeme
    for day_num in display_days:
        day_col_start[day_num] = col_cursor
        col_cursor += day_cols.get(day_num, 1)
    total_cols = col_cursor - 1

    def _col_letter(col_idx):
        """Pretvori 1-based indeks u Excel slovo (A, B, ... Z, AA, AB...)."""
        result = ''
        while col_idx > 0:
            col_idx, rem = divmod(col_idx - 1, 26)
            result = chr(65 + rem) + result
        return result

    # Title row
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=total_cols)
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(name='Arial', bold=True, size=14, color='2C5F8A')
    title_cell.alignment = Alignment(horizontal='center')

    # Header row
    header_row = 3
    c = ws.cell(row=header_row, column=1, value='Vrijeme')
    c.font = header_font
    c.fill = header_fill
    c.alignment = center_align
    c.border = med_border
    ws.column_dimensions['A'].width = 16

    for day_num, day_name in display_days.items():
        header_label = day_name
        if day_dates.get(day_num):
            header_label += f"\n{day_dates[day_num]}"
        start_col = day_col_start[day_num]
        span = day_cols.get(day_num, 1)
        if span > 1:
            ws.merge_cells(start_row=header_row, start_column=start_col,
                           end_row=header_row, end_column=start_col + span - 1)
        c = ws.cell(row=header_row, column=start_col, value=header_label)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center_align
        c.border = med_border
        for sc in range(start_col, start_col + span):
            ws.column_dimensions[_col_letter(sc)].width = max(18, 22 // span + 4)
            if sc != start_col:
                hc = ws.cell(row=header_row, column=sc)
                hc.fill = header_fill
                hc.border = med_border

    # Data rows
    base_row = header_row + 1
    for ts_idx, ts in enumerate(TIME_SLOTS):
        r = base_row + ts_idx
        time_cell = ws.cell(row=r, column=1, value=ts)
        time_cell.font = time_font
        time_cell.fill = time_fill
        time_cell.alignment = center_align
        time_cell.border = med_border
        ws.row_dimensions[r].height = 60

        for day_num in display_days:
            tracks = ci[ts][day_num]
            start_col = day_col_start[day_num]

            for track_idx, info in enumerate(tracks):
                sc = start_col + track_idx

                if info['skip']:
                    continue

                rowspan = info['rowspan']

                if info['entries']:
                    e = info['entries'][0]
                    if rowspan > 1:
                        ws.merge_cells(start_row=r, start_column=sc,
                                       end_row=r + rowspan - 1, end_column=sc)
                    c = ws.cell(row=r, column=sc, value=_format_entry(e))
                    c.font = entry_font
                    c.alignment = center_align
                    c.border = thin_border
                    pc = prof_colors.get(e['professor_id'])
                    if pc:
                        c.fill = PatternFill(
                            start_color=pc['bg'].lstrip('#'),
                            end_color=pc['bg'].lstrip('#'),
                            fill_type='solid'
                        )
                else:
                    c = ws.cell(row=r, column=sc, value='')
                    c.border = thin_border

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='raspored.xlsx'
    )
