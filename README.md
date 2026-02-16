# FOOZOS Raspored

Web aplikacija za upravljanje rasporedom predavanja na Fakultetu za odgojne i obrazovne znanosti u Osijeku (FOOZOS).

## Značajke

- **Redoviti i izvanredni studij** — način studija definiran na razini studijskog programa:
  - **Redoviti**: tablica prikazuje ponedjeljak – petak
  - **Izvanredni**: tablica prikazuje četvrtak – subota, unos po datumu, datumi prikazani u zaglavlju
  - Bez filtera: prikaz ponedjeljak – subota
- **Unos rasporeda** s odabirom dana u tjednu (redoviti) ili datuma (izvanredni), automatskom provjerom konflikata (profesor, učionica, grupa studenata) i mogućnošću potvrde unatoč konfliktima
- **Prikaz rasporeda** po studijskom programu i semestru, po učionici (pojedinačno ili sve učionice) i po profesoru
- **Dvostruki klik za uređivanje** — kliknite dva puta na predavanje u rasporedu za brzo uređivanje
- **Drag & drop** — premjestite predavanje na bilo koji slot povlačenjem mišem
- **Live provjera konflikata** — upozorenja o konfliktima prikazuju se uživo u formi dok unosite podatke
- **Boje po profesoru** — paleta od 200 jedinstvenih boja, automatski dodijeljenih svakom profesoru
- **Spojene ćelije** — predavanja koja traju više slotova prikazana su kao jedna spojena ćelija (rowspan)
- **Razdvajanje pod-stupaca** — preklapajuća predavanja automatski dijele dan na pod-stupce, svaki unos ima vlastiti stupac s točnim rowspanom
- **Podrška za tjedne**: kontinuirano, 1. tjedan, 2. tjedan (s pametnom logikom preklapanja)
- **Eksport** u PDF (A3 landscape), Excel (.xlsx) i ispis (print) — s bojama profesora, spojenim ćelijama i statusima dana
- **Skupni prikaz učionica** — u printu, PDF-u i Excelu svaka učionica dobiva svoju stranicu/sheet
- **Status dana** — dvostruki klik na zaglavlje dana za označavanje kao neradni, praznik ili nenastavni dan
- **Grupni uvoz podataka** — uvoz profesora, studijskih programa i kolegija iz Excel tablice
- **Export/import baze** — preuzmite ili učitajte SQLite bazu za prijenos na drugo računalo
- **CRUD** za akademske godine, studijske programe, kolegije, profesore i učionice
- Moderan dizajn (Bootstrap 5) s responzivnim sučeljem

## Tehnologije

- Python 3 + Flask
- SQLite (bez vanjskog DB servera)
- Bootstrap 5 + Jinja2
- WeasyPrint (PDF) + openpyxl (Excel)

---

## Instalacija na Linux

### Preduvjeti

- Python 3.10 ili noviji
- pip
- Sistemske biblioteke za WeasyPrint (PDF generiranje)

### Korak 1: Instaliraj sistemske ovisnosti

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

**Fedora:**

```bash
sudo dnf install python3 python3-pip python3-virtualenv
sudo dnf install pango cairo gdk-pixbuf2
```

### Korak 2: Kloniraj repozitorij

```bash
git clone https://github.com/kkurilj/FOOZOS_raspored.git
cd FOOZOS_raspored
```

### Korak 3: Kreiraj i aktiviraj virtualno okruženje

```bash
python3 -m venv venv
source venv/bin/activate
```

### Korak 4: Instaliraj Python ovisnosti

```bash
pip install -r requirements.txt
```

### Korak 5: Inicijaliziraj bazu podataka

```bash
flask --app app init-db
```

### Korak 6: Pokreni aplikaciju

```bash
python run.py
```

Otvori **http://127.0.0.1:5000** u pregledniku.

> Za zaustavljanje servera pritisnite `Ctrl+C` u terminalu.

---

## Instalacija na Windows

### Preduvjeti

- Python 3.10 ili noviji (preuzmi s [python.org](https://www.python.org/downloads/))
  - Prilikom instalacije **obavezno označi "Add Python to PATH"**
- Git (preuzmi s [git-scm.com](https://git-scm.com/download/win)) — ili preuzmi ZIP s GitHuba

### Korak 1: Preuzmi projekt

**Opcija A — putem Git-a:**

Otvori Command Prompt ili PowerShell:

```cmd
git clone https://github.com/kkurilj/FOOZOS_raspored.git
cd FOOZOS_raspored
```

**Opcija B — preuzmi ZIP:**

1. Idi na https://github.com/kkurilj/FOOZOS_raspored
2. Klikni zeleni gumb **"Code"** → **"Download ZIP"**
3. Raspakiraj ZIP na željenu lokaciju
4. Otvori Command Prompt i navigiraj u raspakiranu mapu:

```cmd
cd C:\putanja\do\FOOZOS_raspored
```

### Korak 2: Kreiraj i aktiviraj virtualno okruženje

```cmd
python -m venv venv
venv\Scripts\activate
```

> Ako `python` ne radi, pokušaj `py` umjesto `python`.

### Korak 3: Instaliraj Python ovisnosti

```cmd
pip install -r requirements.txt
```

> **Napomena o WeasyPrint-u na Windowsu:** WeasyPrint zahtijeva GTK biblioteke.
> Ako instalacija ili pokretanje javi grešku vezanu uz cairo/pango/GTK, slijedite upute na:
> https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows
>
> Ukratko: instalirajte [MSYS2](https://www.msys2.org/), zatim u MSYS2 terminalu pokrenite:
> ```
> pacman -S mingw-w64-x86_64-pango
> ```
> I dodajte `C:\msys64\mingw64\bin` u PATH varijablu.
>
> **Ako ne trebate PDF export**, aplikacija će raditi i bez WeasyPrint-a — PDF gumb će generirati HTML umjesto PDF-a.

### Korak 4: Inicijaliziraj bazu podataka

```cmd
flask --app app init-db
```

### Korak 5: Pokreni aplikaciju

```cmd
python run.py
```

Otvori **http://127.0.0.1:5000** u pregledniku.

> Za zaustavljanje servera pritisnite `Ctrl+C` u Command Promptu.

---

## Prijenos na drugo računalo

Aplikacija koristi SQLite bazu podataka koja se nalazi u datoteci `instance/raspored.db`. Za prijenos svih podataka na drugo računalo:

1. Na starom računalu: idi na **Baza podataka** u izborniku → klikni **Preuzmi bazu**
2. Na novom računalu: instaliraj aplikaciju prema uputama iznad
3. Idi na **Baza podataka** → klikni **Uvezi bazu** i odaberi preuzetu `.db` datoteku

Alternativno, možete ručno kopirati datoteku `instance/raspored.db` iz jedne instalacije u drugu.

---

## Grupni uvoz podataka

Podatke je moguće grupno uvesti iz Excel (.xlsx) tablica:

| Vrsta podataka | Stupci u Excelu | Primjer |
|---|---|---|
| **Profesori** | Titula, Ime, Prezime | `prof. dr. sc.`, `Ivan`, `Horvat` |
| **Studijski programi** | Šifra, Naziv, Način studiranja | `RPP`, `Rani i predškolski odgoj`, `redoviti` |
| **Kolegiji** | Šifra, Naziv kolegija | `MAT101`, `Matematika 1` |

Gumb **"Uvoz iz Excela"** nalazi se na stranici svake vrste podataka (Profesori, Studijski programi, Kolegiji). Duplikati se automatski preskaču.

---

## Struktura podataka

| Polje | Opis |
|-------|------|
| Akademska godina | npr. 2025./2026. |
| Semestar | zimski/ljetni, broj (1-10) |
| Studijski program | naziv, šifra, način studija (redoviti/izvanredni) |
| Kolegij | naziv, šifra, grupa (A-D), modul (A-C, opcija) |
| Profesor | titula, ime, prezime |
| Učionica | naziv/broj |
| Dan | ponedjeljak - petak (redoviti) / četvrtak - subota (izvanredni) |
| Datum | samo za izvanredne — određuje tjedan i dan u rasporedu |
| Vrijeme | fleksibilno trajanje (početak i završetak, 08:00 - 20:45) |
| Tjedan | kontinuirano, 1. tjedan, 2. tjedan |

## Provjera konflikata

Sustav automatski provjerava:
- **Profesor** ne može biti na dva mjesta istovremeno
- **Učionica** ne može biti dvostruko zauzeta
- **Grupa studenata** ne može imati dva predavanja istovremeno

Logika tjedana: `1. tjedan` i `2. tjedan` se međusobno **ne preklapaju**, ali se oba preklapaju s `kontinuirano`.

Ako postoje konflikti, korisnik ih vidi kao upozorenje (live provjera putem AJAX-a) i može odabrati **"Spremi unatoč konfliktima"** za nasilno spremanje.

---

## Struktura projekta

```
FOOZOS_raspored/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── db.py                    # SQLite konfiguracija i migracije
│   ├── models.py                # Konstante, pomoćne funkcije
│   ├── schema.sql               # Shema baze podataka
│   ├── blueprints/              # Flask blueprints (rute)
│   │   ├── main.py              # Nadzorna ploča
│   │   ├── academic_year.py     # Akademske godine
│   │   ├── study_program.py     # Studijski programi
│   │   ├── professor.py         # Profesori
│   │   ├── classroom.py         # Učionice
│   │   ├── course.py            # Kolegiji
│   │   ├── schedule.py          # Unos rasporeda
│   │   ├── timetable.py         # Prikaz rasporeda + PDF/Excel export
│   │   ├── day_status.py        # Status dana
│   │   └── database.py          # Export/import baze
│   ├── templates/               # Jinja2 predlošci
│   └── static/                  # CSS, JavaScript
├── instance/                    # SQLite baza (raspored.db)
├── config.py                    # Flask konfiguracija
├── run.py                       # Pokretanje servera
├── requirements.txt             # Python ovisnosti
└── README.md
```
