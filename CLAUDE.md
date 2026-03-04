# CLAUDE.md

## Project

Flask web aplikacija za upravljanje rasporedom nastave na FOOZOS-u.
SQLite baza, Blueprint arhitektura, PDF generiranje rasporeda.

## Architecture

```
app/
  blueprints/          # Flask blueprinti (CRUD za svaki entitet)
    academic_year.py
    classroom.py
    course.py
    day_status.py
    professor.py
    schedule.py
    study_program.py
    timetable.py
    database.py        # DB admin (backup/restore)
    main.py
  templates/           # Jinja2 predlošci
  static/              # CSS, JS
  schema.sql           # DDL za SQLite
  db.py                # Database helper
config.py              # Flask konfiguracija
run.py                 # Entry point
```

## Commands

```bash
# Pokretanje
python run.py

# Dependencies
pip install -r requirements.txt
```

## Code Style

- Python 3, Flask blueprinti
- SQLite (instance/raspored.db)
- Jinja2 templates s base.html layoutom
- CSS/JS u static/

## Critical Rules

- Ovo je produkcijska aplikacija — testirati promjene prije deploya
- Baza podataka sadrži stvarne podatke o rasporedu

## Infrastrukturni kontekst

Vault, alati i knowledge base dostupni u `/home/claude-agent/assistant/`:
- Vault: `/home/claude-agent/assistant/vault/`
- Alati: `/home/claude-agent/assistant/tools/`
- Projekt dokumentacija: `vault/Projects/FOOZOS-Raspored/`
