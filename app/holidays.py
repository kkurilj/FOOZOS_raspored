"""Hrvatski državni praznici i blagdani."""

import re
from datetime import date, timedelta

# Fiksni praznici (mjesec, dan, naziv)
FIXED_HOLIDAYS = [
    (1, 1, 'Nova godina'),
    (1, 6, 'Bogojavljanje'),
    (5, 1, 'Praznik rada'),
    (5, 30, 'Dan državnosti'),
    (6, 22, 'Dan antifašističke borbe'),
    (8, 5, 'Dan pobjede i domovinske zahvalnosti'),
    (8, 15, 'Velika Gospa'),
    (11, 1, 'Svi sveti'),
    (11, 18, 'Dan sjećanja na žrtve Domovinskog rata'),
    (12, 25, 'Božić'),
    (12, 26, 'Sveti Stjepan'),
]


def _easter(year):
    """Izračun datuma Uskrsa za godinu (Anonymous Gregorian algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def get_croatian_holidays(year):
    """Vrati listu (date, naziv) svih hrvatskih praznika za kalendarsku godinu."""
    holidays = []

    for month, day, name in FIXED_HOLIDAYS:
        holidays.append((date(year, month, day), name))

    easter = _easter(year)
    holidays.append((easter, 'Uskrs'))
    holidays.append((easter + timedelta(days=1), 'Uskrsni ponedjeljak'))
    holidays.append((easter + timedelta(days=60), 'Tijelovo'))

    holidays.sort(key=lambda h: h[0])
    return holidays


def get_holidays_for_academic_year(ay_name):
    """Parsiraj naziv akademske godine i vrati praznike za njezin raspon.

    Naziv poput "2025/2026" ili "2025./2026." daje raspon
    1.10.2025 – 30.9.2026.

    Vraća listu (iso_date_str, naziv).
    """
    match = re.search(r'(\d{4})\D+(\d{4})', ay_name)
    if not match:
        return []

    first_year = int(match.group(1))
    second_year = int(match.group(2))

    start = date(first_year, 10, 1)
    end = date(second_year, 9, 30)

    result = []
    for year in (first_year, second_year):
        for d, name in get_croatian_holidays(year):
            if start <= d <= end:
                result.append((d.isoformat(), name))

    result.sort(key=lambda h: h[0])
    return result
