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
- **Drag & drop** — custom mouse-based drag s floating klonom, premjestite predavanje na bilo koji slot povlačenjem mišem
- **Live provjera konflikata** — upozorenja o konfliktima prikazuju se uživo u formi dok unosite podatke
- **Boje po profesoru** — paleta od 200 jedinstvenih boja, automatski dodijeljenih svakom profesoru
- **Spojene ćelije** — predavanja koja traju više slotova prikazana su kao jedna spojena ćelija (rowspan) s potpuno ispunjenom bojom
- **Razdvajanje pod-stupaca** — preklapajuća predavanja automatski dijele dan na pod-stupce, svaki unos ima vlastiti stupac s točnim rowspanom na svom vremenskom slotu (web, PDF i Excel)
- **Podrška za tjedne**: kontinuirano, 1. tjedan, 2. tjedan (s pametnom logikom preklapanja)
- **Eksport** u PDF (A3 landscape), Excel (Arial font, centriran tekst) i ispis (print) — s bojama profesora, spojenim ćelijama i statusima dana
- **Status dana** — dvostruki klik na zaglavlje dana za označavanje kao neradni, praznik ili nenastavni dan (prikazuje se i u PDF/Excel exportu)
- **CRUD** za akademske godine, studijske programe, kolegije, profesore i učionice
- **Zadani način studija** — filter automatski postavljen na "redoviti", bez opcije "Svi"
- Moderan dizajn (Bootstrap 5) s responzivnim sučeljem

## Tehnologije

- Python 3 + Flask
- SQLite (bez vanjskog DB servera)
- Bootstrap 5 + Jinja2
- WeasyPrint (PDF) + openpyxl (Excel)

## Instalacija

### Preduvjeti

- Python 3.10+
- pip

### Koraci

```bash
# Kloniraj repozitorij
git clone https://github.com/kkurilj/FOOZOS_raspored.git
cd FOOZOS_raspored

# Kreiraj virtualno okruženje
python3 -m venv venv

# Aktiviraj virtualno okruženje
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate        # Windows

# Instaliraj ovisnosti
pip install -r requirements.txt

# Inicijaliziraj bazu podataka
flask --app app init-db

# Pokreni server
python run.py
```

Otvori **http://127.0.0.1:5000** u pregledniku.

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
