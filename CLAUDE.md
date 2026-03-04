# CLAUDE.md

## IMPORTANT: Always use `web` branch

This project uses the `web` branch as the primary working branch. Never work on `main`.

## Project

Flask web aplikacija za upravljanje rasporedom nastave na FOOZOS-u (Fakultet za odgojne i obrazovne znanosti, Osijek).
Produkcija: https://raspored.foozos.hr

SQLite baza, Blueprint arhitektura, višekorisnički sustav (Super Admin / Admin), Excel export (openpyxl).

## Architecture

```
app/
  __init__.py              # create_app(), blueprint registracija, security middleware
  auth.py                  # Autentikacija (login_required, admin_required, super_admin_required)
  audit.py                 # Audit log helper
  csrf.py                  # CSRF zaštita
  db.py                    # Database helper (get_db, init_app, migrate_db)
  models.py                # Konstante, helperi, conflict checking, grid builder, sort helpers
  schema.sql               # DDL za SQLite (14 tablica)
  blueprints/
    main.py                # Nadzorna ploča, objava rasporeda, upute (/upute), health check
    auth.py                # Prijava / odjava / promjena lozinke
    user.py                # Upravljanje korisnicima + profil
    academic_year.py       # CRUD akademske godine + kopiranje rasporeda
    study_program.py       # CRUD studijski programi (redoviti/izvanredni, vlastiti termini, servisni)
    professor.py           # CRUD profesori + Excel import
    classroom.py           # CRUD učionice
    course.py              # CRUD kolegiji + Excel import + API (filtriranje po programu)
    schedule.py            # CRUD stavke rasporeda + drag&drop + resize + conflict detection + history
    timetable.py           # Prikaz rasporeda (program/učionica/profesor) + Excel + konflikti + objava
    exam.py                # CRUD ispitni rokovi + conflict detection + history
    exam_timetable.py      # Prikaz ispitnih rokova + Excel + objava
    day_status.py          # Status dana (po danu u tjednu i po datumu) + HR praznici
    database.py            # DB admin (export/import/backup)
    audit_log.py           # Evidencija promjena
    analytics.py           # Statistika posjeta
  templates/               # Jinja2 predlošci (base.html layout)
    guide.html             # Upute za rad — ažurirati kad se dodaju nove značajke
  static/
    css/style.css
    js/app.js
    img/logo.jpg
config.py                  # Flask Config (SECRET_KEY, DATABASE, SESSION)
run.py                     # Entry point (port 5000)
requirements.txt           # Flask, openpyxl, xlrd, Werkzeug
deploy/                    # Apache2 + Gunicorn + backup skripta
```

## Database Schema

14 tablica: `academic_year`, `study_program`, `professor`, `classroom`, `course`, `schedule_entry`, `schedule_history`, `exam_entry`, `exam_history`, `day_status`, `day_status_date`, `user`, `login_attempt`, `audit_log`

- Baza: `instance/raspored.db` (SQLite)
- `schedule_entry` je središnja tablica s FK na academic_year, study_program, course, professor, classroom
- `exam_entry` zasebna tablica za ispitne rokove
- `user` s ulogama: super_admin, admin
- `day_status` (po danu u tjednu) + `day_status_date` (po datumu)

## Key Domain Concepts

- **study_mode**: `redoviti` | `izvanredni` — različiti dani i vremenski slotovi
- **week_type**: `kontinuirano` | `1. tjedan` | `2. tjedan` — za A/B tjedne
- **teaching_form**: `predavanja` | `seminari` | `vježbe`
- **semester_type**: `zimski` | `ljetni`
- **groups**: A, B, C, D, E
- **modules**: A, B, C
- **is_service**: servisni programi (narančasta boja)
- **custom_start_time/end_time/slot_minutes**: vlastiti termini za programe
- **is_published**: objava stavki (neobjavljene vidljive samo adminima)
- **has_conflict**: automatski označene stavke s konfliktima
- **Conflict detection**: profesor, učionica, grupa, status dana
- **Exam types**: Ispit, Obrana završnog/diplomskog/doktorskog rada

## Commands

```bash
# Development
python run.py
# → http://127.0.0.1:5000

# Dependencies
pip install -r requirements.txt

# Init DB
flask --app app init-db

# Default login: admin / admin (obavezna promjena lozinke)
```

## Code Style

- Python 3, Flask blueprinti, factory pattern (create_app)
- SQLite s raw SQL (ne ORM)
- Jinja2 templates s base.html layoutom
- Komentari na hrvatskom u domenskom kodu
- Hrvatski sort (č, ć, đ, š, ž) u models.py
- CSRF zaštita na svim POST zahtjevima
- Audit log za sve admin akcije

## Critical Rules

- Produkcijska aplikacija na raspored.foozos.hr — testirati promjene prije deploya
- Baza sadrži stvarne podatke o rasporedu nastave
- Conflict detection u models.py — ne zaobilaziti
- Ne mijenjati schema.sql bez migracije postojećih podataka (migrate_db u db.py)
- guide.html (Upute za rad) treba ažurirati kad se dodaju nove značajke
- Uvijek raditi na `web` branchu

## Infrastrukturni kontekst

Vault, alati i knowledge base dostupni u `/home/claude-agent/assistant/`:
- Vault: `/home/claude-agent/assistant/vault/`
- Alati: `/home/claude-agent/assistant/tools/`
- Projekt dokumentacija: `vault/Projects/FOOZOS-Raspored/`
