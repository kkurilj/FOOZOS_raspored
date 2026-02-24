import re
from flask import Blueprint, render_template, request
from app.db import get_db
from app.auth import login_required

bp = Blueprint('analytics', __name__)


def parse_user_agent(ua):
    """Parsiraj User-Agent string i vrati (device_type, browser, os)."""
    if not ua:
        return 'nepoznato', 'nepoznato', 'nepoznato'
    ua_lower = ua.lower()

    # Device type
    if any(kw in ua_lower for kw in ('mobile', 'android', 'iphone', 'ipod')):
        if 'tablet' in ua_lower or 'ipad' in ua_lower:
            device_type = 'tablet'
        else:
            device_type = 'mobitel'
    elif 'ipad' in ua_lower or ('tablet' in ua_lower):
        device_type = 'tablet'
    elif any(kw in ua_lower for kw in ('bot', 'crawl', 'spider', 'slurp', 'wget', 'curl')):
        device_type = 'bot'
    else:
        device_type = 'desktop'

    # Browser
    if 'edg/' in ua_lower or 'edge/' in ua_lower:
        browser = 'Edge'
    elif 'opr/' in ua_lower or 'opera' in ua_lower:
        browser = 'Opera'
    elif 'chrome/' in ua_lower and 'chromium' not in ua_lower:
        browser = 'Chrome'
    elif 'safari/' in ua_lower and 'chrome/' not in ua_lower:
        browser = 'Safari'
    elif 'firefox/' in ua_lower:
        browser = 'Firefox'
    elif 'msie' in ua_lower or 'trident/' in ua_lower:
        browser = 'IE'
    else:
        browser = 'ostalo'

    # OS
    if 'windows' in ua_lower:
        os_name = 'Windows'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower or 'ipod' in ua_lower:
        os_name = 'iOS'
    elif 'mac os' in ua_lower or 'macintosh' in ua_lower:
        os_name = 'macOS'
    elif 'android' in ua_lower:
        os_name = 'Android'
    elif 'linux' in ua_lower:
        os_name = 'Linux'
    elif 'cros' in ua_lower:
        os_name = 'ChromeOS'
    else:
        os_name = 'ostalo'

    return device_type, browser, os_name


# Mapiranje URL putanja u čitljive nazive
PATH_LABELS = {
    '/': 'Nadzorna ploča',
    '/timetable/program': 'Raspored po programu',
    '/timetable/professor': 'Raspored po profesoru',
    '/timetable/classroom': 'Raspored po učionici',
    '/schedule/': 'Unos stavki',
    '/analytics/': 'Statistika posjeta',
}


def friendly_path(path):
    """Pretvori URL putanju u čitljiv naziv."""
    for prefix, label in PATH_LABELS.items():
        if path == prefix or (prefix.endswith('/') and path.startswith(prefix)):
            return label
    return path


@bp.route('/')
@login_required
def index():
    db = get_db()

    # Ukupni brojevi
    total = db.execute('SELECT COUNT(*) FROM page_visit').fetchone()[0]
    total_unique = db.execute('SELECT COUNT(DISTINCT ip_address) FROM page_visit').fetchone()[0]

    today = db.execute(
        "SELECT COUNT(*) FROM page_visit WHERE date(visited_at) = date('now', 'localtime')"
    ).fetchone()[0]
    today_unique = db.execute(
        "SELECT COUNT(DISTINCT ip_address) FROM page_visit WHERE date(visited_at) = date('now', 'localtime')"
    ).fetchone()[0]

    week = db.execute(
        "SELECT COUNT(*) FROM page_visit WHERE visited_at >= datetime('now', 'localtime', '-7 days')"
    ).fetchone()[0]
    week_unique = db.execute(
        "SELECT COUNT(DISTINCT ip_address) FROM page_visit WHERE visited_at >= datetime('now', 'localtime', '-7 days')"
    ).fetchone()[0]

    month = db.execute(
        "SELECT COUNT(*) FROM page_visit WHERE visited_at >= datetime('now', 'localtime', '-30 days')"
    ).fetchone()[0]
    month_unique = db.execute(
        "SELECT COUNT(DISTINCT ip_address) FROM page_visit WHERE visited_at >= datetime('now', 'localtime', '-30 days')"
    ).fetchone()[0]

    # Posjeti po danima (zadnjih 30 dana)
    daily_rows = db.execute('''
        SELECT date(visited_at) as day, COUNT(*) as cnt, COUNT(DISTINCT ip_address) as unique_cnt
        FROM page_visit
        WHERE visited_at >= datetime('now', 'localtime', '-30 days')
        GROUP BY date(visited_at)
        ORDER BY day
    ''').fetchall()
    daily_labels = [row['day'] for row in daily_rows]
    daily_counts = [row['cnt'] for row in daily_rows]
    daily_unique = [row['unique_cnt'] for row in daily_rows]

    # Top 10 stranica
    top_pages = db.execute('''
        SELECT path, COUNT(*) as cnt
        FROM page_visit
        GROUP BY path
        ORDER BY cnt DESC
        LIMIT 10
    ''').fetchall()
    top_pages_data = [{'path': friendly_path(row['path']), 'raw_path': row['path'], 'count': row['cnt']} for row in top_pages]

    # Raspodjela po tipu uređaja
    devices = db.execute('''
        SELECT device_type, COUNT(*) as cnt
        FROM page_visit
        WHERE device_type IS NOT NULL
        GROUP BY device_type
        ORDER BY cnt DESC
    ''').fetchall()
    device_labels = [row['device_type'] for row in devices]
    device_counts = [row['cnt'] for row in devices]

    # Raspodjela po pregledniku
    browsers = db.execute('''
        SELECT browser, COUNT(*) as cnt
        FROM page_visit
        WHERE browser IS NOT NULL
        GROUP BY browser
        ORDER BY cnt DESC
    ''').fetchall()
    browser_labels = [row['browser'] for row in browsers]
    browser_counts = [row['cnt'] for row in browsers]

    # Raspodjela po OS-u
    os_rows = db.execute('''
        SELECT os, COUNT(*) as cnt
        FROM page_visit
        WHERE os IS NOT NULL
        GROUP BY os
        ORDER BY cnt DESC
    ''').fetchall()
    os_labels = [row['os'] for row in os_rows]
    os_counts = [row['cnt'] for row in os_rows]

    # Posjeti po satu (distribucija kroz dan)
    hourly = db.execute('''
        SELECT CAST(strftime('%H', visited_at) AS INTEGER) as hour, COUNT(*) as cnt
        FROM page_visit
        GROUP BY hour
        ORDER BY hour
    ''').fetchall()
    hourly_labels = [f"{row['hour']:02d}:00" for row in hourly]
    hourly_counts = [row['cnt'] for row in hourly]

    # Zadnjih 50 posjeta
    recent = db.execute('''
        SELECT path, ip_address, device_type, browser, os, is_admin, visited_at
        FROM page_visit
        ORDER BY visited_at DESC
        LIMIT 50
    ''').fetchall()
    recent_visits = [{
        'path': friendly_path(row['path']),
        'raw_path': row['path'],
        'ip': row['ip_address'],
        'device': row['device_type'],
        'browser': row['browser'],
        'os': row['os'],
        'is_admin': row['is_admin'],
        'time': row['visited_at'],
    } for row in recent]

    return render_template('analytics/index.html',
        total=total, total_unique=total_unique,
        today=today, today_unique=today_unique,
        week=week, week_unique=week_unique,
        month=month, month_unique=month_unique,
        daily_labels=daily_labels, daily_counts=daily_counts, daily_unique=daily_unique,
        top_pages=top_pages_data,
        device_labels=device_labels, device_counts=device_counts,
        browser_labels=browser_labels, browser_counts=browser_counts,
        os_labels=os_labels, os_counts=os_counts,
        hourly_labels=hourly_labels, hourly_counts=hourly_counts,
        recent_visits=recent_visits,
    )
