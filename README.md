# FOOZOS Raspored

Web aplikacija za upravljanje rasporedom predavanja na Fakultetu za odgojne i obrazovne znanosti u Osijeku (FOOZOS).

## Značajke

### Raspored i prikaz
- **Redoviti i izvanredni studij** — način studija definiran na razini studijskog programa:
  - **Redoviti**: ponedjeljak – petak, vremenski slotovi 08:00 – 19:30 (po 45 min s pauzama)
  - **Izvanredni**: četvrtak – subota, vremenski slotovi 08:30 – 21:00 (16 slotova), unos po datumu, datumi prikazani u zaglavlju
  - Forma za unos automatski prilagođava dostupna vremena prema načinu studija odabranog programa
  - Bez filtera: prikaz ponedjeljak – subota
- **Prikaz rasporeda** po studijskom programu i semestru, po učionici (pojedinačno ili sve učionice) i po profesoru
  - Obvezni filteri označeni crvenom zvjezdicom (`*`) u svakom prikazu
  - Za izvanredni: grupiranje po tjednima; u prikazu po učionici grupiranje po učionici i tjednu (npr. "Učionica 22 | 26.02. - 28.02.2026.")
- **Spojene ćelije** — predavanja koja traju više slotova prikazana su kao jedna spojena ćelija (rowspan)
- **Razdvajanje pod-stupaca** — preklapajuća predavanja automatski dijele dan na pod-stupce, svaki unos ima vlastiti stupac s točnim rowspanom
- **Splitanje po tjednima** — ako dan sadrži unose za "1. tjedan" ili "2. tjedan", stupac se automatski dijeli na dva pod-stupca (1. tj / 2. tj); "kontinuirano" unosi se prikazuju preko oba pod-stupca
- **Splitanje ćelija za paralelne stavke** — stavke u istom terminu s različitim grupama ili učionicama prikazuju se side-by-side unutar iste ćelije umjesto dodavanja extra stupaca za cijeli dan; radi u web prikazu, printu i Excel exportu
- **Boje po studijskom programu** — paleta od 200 jedinstvenih boja, svaki studijski program ima svoju konzistentnu boju kroz cijelu aplikaciju (web, Excel)
- **Podrška za tjedne**: kontinuirano, 1. tjedan, 2. tjedan (s pametnom logikom preklapanja)
- **Status dana** — označavanje dana kao neradni, praznik ili nenastavni; dva načina:
  - **Po danu u tjednu** — npr. "svaki ponedjeljak" (korisno za redovite)
  - **Po specifičnom datumu** — npr. "25.12.2025." (korisno za izvanredne i konkretne praznike)
  - Status po datumu ima prioritet nad statusom po danu u tjednu
  - Dvostruki klik na zaglavlje dana u rasporedu otvara dijalog za postavljanje statusa; za dane s datumom automatski se sprema kao date-specifični status

### Unos i uređivanje
- **Unos rasporeda** s odabirom dana u tjednu (redoviti) ili datuma (izvanredni), automatskom provjerom konflikata (profesor, učionica, grupa studenata) i mogućnošću potvrde unatoč konfliktima
- **Napomena** — opcionalno tekstualno polje na svakoj stavci rasporeda, prikazano crvenom bojom i podebljano (web prikaz i Excel export)
- **Live provjera konflikata** — upozorenja o konfliktima prikazuju se uživo u formi dok unosite podatke
- **Dvostruki klik za uređivanje** — kliknite dva puta na predavanje u rasporedu za brzo uređivanje; iz forme za uređivanje moguće je i obrisati stavku
- **Drag & drop** — premjestite predavanje na bilo koji slot povlačenjem mišem
- **Prikaz konflikata** — poseban prikaz (Unos rasporeda > Konflikti) koji prikazuje samo stavke rasporeda s konfliktima, dostupan adminima
- **Slobodne učionice** — na stranici konflikata i u formi za uređivanje, gumb prikazuje popis učionica slobodnih u tom terminu; klik na učionicu u formi automatski je odabire
- **Popis stavki** — sortiran od najnovije do najstarije (najnovija na vrhu)

### Objava rasporeda
- **Objava rasporeda** — novi unosi i izmjene nisu vidljivi javnosti dok admin ne klikne "Objavi raspored" na nadzornoj ploči
- Admini uvijek vide sve stavke (objavljene i neobjavljene)
- Neprijavljeni korisnici vide samo objavljene stavke
- Nadzorna ploča prikazuje broj neobjavljenih stavki s gumbom za objavu

### Kopiranje akademske godine
- **Kopiranje rasporeda** — sve stavke iz jedne akademske godine mogu se kopirati u drugu
- Kopiraju se i statusi dana (po danu u tjednu i po specifičnom datumu)
- Kopirane stavke su neobjavljene (zahtijevaju objavu) i bez konflikata za pregled prije objave
- Gumb za kopiranje dostupan pored svake akademske godine

### Izvoz i ispis
- **Excel (.xlsx)** — formatirani raspored s bojama studijskih programa, spojenim ćelijama, statusima dana i napomenama
  - Naziv datoteke ovisi o prikazu: `FOOZOS_RASPORED_STUDIJI_DD_MM_YYYY.xlsx`, `FOOZOS_RASPORED_UCIONICE_DD_MM_YYYY.xlsx`, `FOOZOS_RASPORED_PROFESORI_DD_MM_YYYY.xlsx`
  - Za izvanredni studij naziv sadrži sufiks: `FOOZOS_RASPORED_STUDIJI_IZVANREDNI_DD_MM_YYYY.xlsx`
  - Za izvanredni prikaz: svaki tjedan (ili kombinacija učionica × tjedan) generira se kao zasebni Excel sheet
- **Ispis (print)** — optimizirano za pejzažni format, svaki semestar/učionica na zasebnoj stranici, bez URL-ova i metapodataka preglednika
- **Skupni prikaz učionica** — u printu i Excelu svaka učionica dobiva svoju stranicu/sheet

### Uvoz podataka
- **Grupni uvoz podataka** — uvoz profesora, studijskih programa i kolegija iz Excel tablice
- **Export/import baze** — preuzmite ili učitajte SQLite bazu za prijenos na drugo računalo; pri uvozu automatski se kreira backup postojeće baze i pokreću migracije
- **Popis automatskih backupova** — na stranici Baza podataka prikazuju se dnevni automatski backupovi s mogućnošću preuzimanja

### Korisnici i sigurnost
- **Višekorisnički sustav** — uloge Super Admin i Admin:
  - **Super Admin** — upravljanje korisnicima, export/import baze, evidencija promjena, svi ostali podaci
  - **Admin** — unos i uređivanje rasporeda i podataka (programi, kolegiji, profesori, učionice)
  - Svaki korisnik može uređivati vlastiti profil (ime za prikaz, lozinka)
  - Javnost (neprijavljeni korisnici) može samo pregledavati objavljene rasporede
- **Automatska odjava** — sesija istječe nakon 30 minuta neaktivnosti
- **Zaštita od brute-force napada** — blokada prijave nakon 3 neuspjela pokušaja na 15 minuta (20 pokušaja za IP adrese iz pouzdane mreže)
- **CSRF zaštita** — svi POST zahtjevi zaštićeni tokenom
- **Sigurnosni HTTP zaglavlja** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options i dr.

### Praćenje promjena
- **Povijest promjena** — zadnjih 30 promjena nad stavkama rasporeda s mogućnošću poništavanja (undo)
- **Evidencija promjena (audit log)** — potpuni zapis svih akcija u sustavu (prijave, odjave, kreiranja, uređivanja, brisanja, objave, kopiranja) s izvozom u CSV
- **CRUD** za akademske godine, studijske programe (s elementom studija), kolegije, profesore i učionice
- **Potvrda kaskadnog brisanja** — brisanje akademske godine, programa, kolegija, profesora ili učionice zahtijeva potvrdu kroz modal s upozorenjem o kaskadnom brisanju povezanih stavki rasporeda
- **Zaštita zadane akademske godine** — zadana akademska godina se ne može obrisati dok je postavljena kao zadana

### Ostalo
- **Kolegiji vezani uz studijski program** — svaki kolegij pripada jednom studijskom programu i elementu studija; u formi za unos rasporeda kolegiji se automatski filtriraju prema odabranom programu
- **Sortiranje padajućih izbornika** — hrvatsko abecedno sortiranje (č, ć, đ, š, ž na ispravnom mjestu) + prirodno sortiranje učionica (1, 2, 10, 22, ne 1, 10, 2, 22)
- **Mobilni prikaz** — na mobilnim uređajima raspored se prikazuje dan po dan s tabovima
- **FOOZOS logo** u navigacijskoj traci
- Moderan dizajn (Bootstrap 5) s responzivnim sučeljem

## Tehnologije

- Python 3 + Flask
- SQLite (bez vanjskog DB servera)
- Bootstrap 5 + Bootstrap Icons + Jinja2
- openpyxl (Excel export)
- Werkzeug (sigurnost, hashiranje lozinki)

---

## Instalacija na Linux

### Preduvjeti

- Python 3.10 ili noviji
- pip

### Korak 1: Instaliraj sistemske ovisnosti

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Fedora:**

```bash
sudo dnf install python3 python3-pip python3-virtualenv
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

### Početna prijava

Pri prvom pokretanju automatski se kreira Super Admin korisnik:

- **Korisničko ime:** `admin`
- **Lozinka:** `admin`

Preporučuje se promijeniti lozinku nakon prve prijave (Profil → Nova lozinka).

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

### Početna prijava

Pri prvom pokretanju automatski se kreira Super Admin korisnik:

- **Korisničko ime:** `admin`
- **Lozinka:** `admin`

Preporučuje se promijeniti lozinku nakon prve prijave (Profil → Nova lozinka).

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
| **Studijski programi** | Šifra, Naziv, Način studiranja, Element studija (opcijski) | `RPP`, `Rani i predškolski odgoj`, `redoviti`, `Informatika` |
| **Kolegiji** | Šifra, Naziv kolegija (uz odabir studijskog programa) | `MAT101`, `Matematika 1` |

Gumb **"Uvoz iz Excela"** nalazi se na stranici svake vrste podataka (Profesori, Studijski programi, Kolegiji). Duplikati se automatski preskaču.

---

## Struktura podataka

| Polje | Opis |
|-------|------|
| Akademska godina | npr. 2025./2026. |
| Semestar | zimski/ljetni, broj (1-10) |
| Studijski program | naziv, šifra, način studija (redoviti/izvanredni), element studija |
| Kolegij | naziv, šifra, studijski program, grupa (A-E), modul (A-C, opcija) |
| Profesor | titula, ime, prezime |
| Učionica | naziv/broj |
| Dan | ponedjeljak - petak (redoviti) / četvrtak - subota (izvanredni) |
| Datum | samo za izvanredne — određuje tjedan i dan u rasporedu |
| Oblik nastave | predavanja, seminari, vježbe |
| Vrijeme | redoviti: 08:00-19:30 (12 slotova), izvanredni: 08:30-21:00 (16 slotova) |
| Tjedan | kontinuirano, 1. tjedan, 2. tjedan |
| Napomena | opcionalni tekst uz stavku rasporeda |

## Provjera konflikata

Sustav automatski provjerava:
- **Profesor** ne može biti na dva mjesta istovremeno
- **Učionica** ne može biti dvostruko zauzeta
- **Grupa studenata** ne može imati dva predavanja istovremeno

Logika tjedana: `1. tjedan` i `2. tjedan` se međusobno **ne preklapaju**, ali se oba preklapaju s `kontinuirano`.

Ako postoje konflikti, korisnik ih vidi kao upozorenje (live provjera putem AJAX-a) i može odabrati **"Spremi unatoč konfliktima"** za nasilno spremanje.

Poseban prikaz **Konflikti** (Unos rasporeda > Konflikti) prikazuje sve stavke s konfliktima na jednom mjestu, s mogućnošću direktnog uređivanja.

---

## Sigurnost

- **Hashirane lozinke** — Werkzeug PBKDF2 (nikad se ne spremaju u čistom tekstu)
- **CSRF zaštita** — svi POST zahtjevi zaštićeni jedinstvenim tokenom
- **Rate limiting** — blokada prijave nakon 3 neuspjela pokušaja na 15 minuta (20 pokušaja za pouzdanu mrežu 193.198.137.0/27)
- **Automatska odjava** — sesija istječe nakon 30 minuta neaktivnosti, obnavlja se sa svakom akcijom
- **Zaštita od session fixation** — regeneracija sesije nakon uspješne prijave
- **Sigurnosni HTTP zaglavlja** — Content-Security-Policy, Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy
- **Secure cookies** — HttpOnly, SameSite=Lax, Secure u produkciji
- **Open redirect zaštita** — validacija URL-a nakon prijave
- **Podrška za reverse proxy** — ProxyFix za ispravno čitanje IP adrese klijenta iza Apache/Nginx
- **SRI (Subresource Integrity)** — provjera integriteta vanjskih CDN resursa

---

## Produkcija

Aplikacija je u produkciji na **https://raspored.foozos.hr**.

Za postavljanje na vlastiti server pogledajte detaljne upute u [`deploy/DEPLOY.md`](deploy/DEPLOY.md).

Stack: **Apache2** (reverse proxy + SSL) → **Gunicorn** (WSGI server) → **Flask**

Automatski dnevni backup baze (cron, 30 dana retencija) — detalji u uputama za deploy.

---

## Struktura projekta

```
FOOZOS_raspored/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── auth.py                  # Autentikacija (decoratori, helperi)
│   ├── audit.py                 # Audit log helper
│   ├── csrf.py                  # CSRF zaštita
│   ├── db.py                    # SQLite konfiguracija i migracije
│   ├── models.py                # Konstante, pomoćne funkcije, upiti
│   ├── schema.sql               # Shema baze podataka
│   ├── blueprints/              # Flask blueprints (rute)
│   │   ├── main.py              # Nadzorna ploča + objava rasporeda
│   │   ├── auth.py              # Prijava / odjava / promjena lozinke
│   │   ├── user.py              # Upravljanje korisnicima + profil
│   │   ├── academic_year.py     # Akademske godine + kopiranje rasporeda
│   │   ├── study_program.py     # Studijski programi
│   │   ├── professor.py         # Profesori
│   │   ├── classroom.py         # Učionice
│   │   ├── course.py            # Kolegiji
│   │   ├── schedule.py          # Unos/uređivanje rasporeda + povijest promjena
│   │   ├── timetable.py         # Prikaz rasporeda + Excel export + konflikti
│   │   ├── day_status.py        # Status dana
│   │   ├── database.py          # Export/import baze
│   │   └── audit_log.py         # Evidencija promjena (audit log)
│   ├── templates/               # Jinja2 predlošci
│   └── static/                  # CSS, JavaScript
├── deploy/                      # Produkcijska konfiguracija
│   ├── DEPLOY.md                # Upute za postavljanje na server
│   ├── gunicorn.service         # Systemd servis za Gunicorn
│   ├── apache2.conf             # Apache2 VirtualHost konfiguracija
│   └── backup.sh                # Skripta za dnevni backup baze
├── instance/                    # SQLite baza (raspored.db)
├── config.py                    # Flask konfiguracija
├── run.py                       # Pokretanje servera
├── requirements.txt             # Python ovisnosti
└── README.md
```
