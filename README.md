# FOOZOS Raspored

Web aplikacija za upravljanje rasporedom predavanja na Fakultetu za odgojne i obrazovne znanosti u Osijeku (FOOZOS).

## Značajke

- **Unos rasporeda** s odabirom dana u tjednu, automatskom provjerom konflikata (profesor, učionica, grupa studenata) i mogućnošću potvrde unatoč konfliktima
- **Prikaz rasporeda** po studijskom programu i semestru, po učionici i po profesoru
- **Dvostruki klik za uređivanje** — kliknite dva puta na predavanje u rasporedu za brzo uređivanje
- **Drag & drop** — premjestite predavanje na drugi dan ili termin povlačenjem mišem, s automatskom provjerom konflikata
- **Live provjera konflikata** — upozorenja o konfliktima prikazuju se uživo u formi dok unosite podatke i traju dok ih korisnik ne potvrdi
- **Boje po profesoru** — paleta od 200 jedinstvenih boja, automatski dodijeljenih svakom profesoru
- **Spojene ćelije** — predavanja koja traju više slotova prikazana su kao jedna spojena ćelija (rowspan) s potpuno ispunjenom bojom
- **Paralelna predavanja** — više predavanja u istom terminu prikazuju se jedno pored drugog (side-by-side) u webu, PDF-u i Excelu (sub-stupci)
- **Podrška za tjedne**: kontinuirano, 1. tjedan, 2. tjedan (s pametnom logikom preklapanja)
- **7 dana u tjednu** (ponedjeljak - nedjelja)
- **Eksport** u PDF (A3 landscape), Excel (Arial font) i ispis (print) — s bojama profesora i spojenim ćelijama
- **CRUD** za akademske godine, studijske programe, kolegije, profesore i učionice
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
| Studijski program | naziv i šifra |
| Kolegij | naziv, šifra, grupa (A-D), modul (A-C, opcija) |
| Profesor | titula, ime, prezime |
| Učionica | naziv/broj |
| Dan | ponedjeljak - nedjelja |
| Vrijeme | fleksibilno trajanje (početak i završetak, 08:00 - 20:45) |
| Tjedan | kontinuirano, 1. tjedan, 2. tjedan |

## Provjera konflikata

Sustav automatski provjerava:
- **Profesor** ne može biti na dva mjesta istovremeno
- **Učionica** ne može biti dvostruko zauzeta
- **Grupa studenata** ne može imati dva predavanja istovremeno

Logika tjedana: `1. tjedan` i `2. tjedan` se međusobno **ne preklapaju**, ali se oba preklapaju s `kontinuirano`.

Ako postoje konflikti, korisnik ih vidi kao trajno upozorenje (live provjera putem AJAX-a) i može odabrati **"Spremi unatoč konfliktima"** za nasilno spremanje. Upozorenja ostaju vidljiva dok korisnik ne riješi konflikt ili ih eksplicitno potvrdi.
