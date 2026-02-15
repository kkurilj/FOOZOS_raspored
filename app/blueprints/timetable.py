import io
from flask import Blueprint, render_template, request, make_response, send_file
from app.db import get_db
from app.models import DAYS, TIME_SLOTS, WEEK_TYPES, SEMESTER_TYPES, get_schedule_entries, build_timetable_grid

bp = Blueprint('timetable', __name__)


def get_filter_options():
    db = get_db()
    return {
        'academic_years': db.execute('SELECT * FROM academic_year ORDER BY name DESC').fetchall(),
        'study_programs': db.execute('SELECT * FROM study_program ORDER BY name').fetchall(),
        'professors': db.execute('SELECT * FROM professor ORDER BY last_name, first_name').fetchall(),
        'classrooms': db.execute('SELECT * FROM classroom ORDER BY name').fetchall(),
        'week_types': WEEK_TYPES,
        'semester_types': SEMESTER_TYPES,
        'days': DAYS,
        'time_slots': TIME_SLOTS,
    }


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
        }
        if filters.get('study_program_id'):
            prog = db.execute('SELECT * FROM study_program WHERE id = ?',
                              (filters['study_program_id'],)).fetchone()
            if prog:
                sem_num = filters.get('semester_number', '')
                sem_type = filters.get('semester_type', '')
                title = f"Raspored - {prog['name']} - {sem_num}. semestar ({sem_type})"

    elif view_type == 'classroom':
        filters = {
            'academic_year_id': request.args.get('academic_year_id', type=int),
            'classroom_id': request.args.get('classroom_id', type=int),
            'week_type': request.args.get('week_type'),
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
        }
        if filters.get('professor_id'):
            prof = db.execute('SELECT * FROM professor WHERE id = ?',
                              (filters['professor_id'],)).fetchone()
            if prof:
                title = f"Raspored - {prof['title']} {prof['first_name']} {prof['last_name']}".strip()

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
    }

    entries = get_schedule_entries(filters) if any(filters.values()) else []
    grid = build_timetable_grid(entries)

    return render_template(
        'timetable/by_program.html',
        grid=grid, entries=entries, filters=filters,
        **get_filter_options()
    )


@bp.route('/classroom')
def by_classroom():
    filters = {
        'academic_year_id': request.args.get('academic_year_id', type=int),
        'classroom_id': request.args.get('classroom_id', type=int),
        'week_type': request.args.get('week_type'),
    }

    entries = get_schedule_entries(filters) if filters.get('classroom_id') else []
    grid = build_timetable_grid(entries)

    return render_template(
        'timetable/by_classroom.html',
        grid=grid, entries=entries, filters=filters,
        **get_filter_options()
    )


@bp.route('/professor')
def by_professor():
    filters = {
        'academic_year_id': request.args.get('academic_year_id', type=int),
        'professor_id': request.args.get('professor_id', type=int),
        'week_type': request.args.get('week_type'),
    }

    entries = get_schedule_entries(filters) if filters.get('professor_id') else []
    grid = build_timetable_grid(entries)

    return render_template(
        'timetable/by_professor.html',
        grid=grid, entries=entries, filters=filters,
        **get_filter_options()
    )


@bp.route('/pdf')
def export_pdf():
    view_type = request.args.get('view', 'program')
    title, filters = _build_title_and_filters(view_type)

    entries = get_schedule_entries(filters) if any(filters.values()) else []
    grid = build_timetable_grid(entries)

    html = render_template(
        'pdf/timetable_pdf.html',
        grid=grid, title=title, view_type=view_type,
        days=DAYS, time_slots=TIME_SLOTS
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

    entries = get_schedule_entries(filters) if any(filters.values()) else []
    grid = build_timetable_grid(entries)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Raspored'

    # Styles
    header_font = Font(bold=True, color='FFFFFF', size=10)
    header_fill = PatternFill(start_color='2C5F8A', end_color='2C5F8A', fill_type='solid')
    time_fill = PatternFill(start_color='F0F2F5', end_color='F0F2F5', fill_type='solid')
    time_font = Font(bold=True, size=9)
    entry_font = Font(size=8)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
    top_align = Alignment(vertical='top', wrap_text=True)

    # Title row
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=1 + len(DAYS))
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(bold=True, size=14, color='2C5F8A')
    title_cell.alignment = Alignment(horizontal='center')

    # Header row
    row = 3
    ws.cell(row=row, column=1, value='Vrijeme').font = header_font
    ws.cell(row=row, column=1).fill = header_fill
    ws.cell(row=row, column=1).alignment = center_align
    ws.cell(row=row, column=1).border = thin_border
    ws.column_dimensions['A'].width = 16

    for i, (day_num, day_name) in enumerate(DAYS.items(), start=2):
        cell = ws.cell(row=row, column=i, value=day_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        col_letter = chr(64 + i) if i <= 26 else None
        if col_letter:
            ws.column_dimensions[col_letter].width = 22

    # Data rows
    for ts in TIME_SLOTS:
        row += 1
        time_cell = ws.cell(row=row, column=1, value=ts)
        time_cell.font = time_font
        time_cell.fill = time_fill
        time_cell.alignment = center_align
        time_cell.border = thin_border

        for day_num in DAYS:
            col = day_num + 1
            cell_entries = grid[ts][day_num]
            slot_start = ts.split(' - ')[0]
            if cell_entries:
                lines = []
                for e in cell_entries:
                    if e['start_time'] != slot_start:
                        continue
                    parts = [e['course_name'], f"{e['start_time']}-{e['end_time']}"]
                    if view_type != 'professor':
                        prof = f"{e['title']} {e['first_name']} {e['last_name']}".strip()
                        parts.append(prof)
                    if view_type != 'classroom':
                        parts.append(e['classroom_name'])
                    if view_type in ('classroom', 'professor'):
                        parts.append(f"{e['program_name']} ({e['semester_number']}.sem)")
                    parts.append(f"Gr.{e['group_name']}")
                    if e['module_name']:
                        parts.append(f"M:{e['module_name']}")
                    if e['week_type'] != 'kontinuirano':
                        parts.append(f"[{e['week_type']}]")
                    lines.append(' | '.join(parts))
                cell = ws.cell(row=row, column=col, value='\n'.join(lines))
            else:
                cell = ws.cell(row=row, column=col, value='')

            cell.font = entry_font
            cell.alignment = top_align
            cell.border = thin_border

        ws.row_dimensions[row].height = 60

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='raspored.xlsx'
    )
