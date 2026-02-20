# Postavljanje na produkcijski server (Apache2 + Gunicorn)

## 1. Priprema servera

```bash
sudo apt update
sudo apt install apache2 python3-venv libapache2-mod-proxy-html sqlite3
sudo a2enmod proxy proxy_http ssl headers rewrite
sudo mkdir -p /var/log/raspored
sudo chown www-data:www-data /var/log/raspored
```

## 2. Aplikacija

```bash
sudo mkdir -p /var/www/html/FOOZOS_raspored
sudo cp -r . /var/www/html/FOOZOS_raspored/
cd /var/www/html/FOOZOS_raspored
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo chown -R www-data:www-data /var/www/html/FOOZOS_raspored
```

## 3. Gunicorn servis

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/raspored.service
sudo systemctl daemon-reload
sudo systemctl enable raspored
sudo systemctl start raspored
```

Konfiguracija uključuje:
- 3 workera (prilagoditi broju CPU jezgri: `2 * CPU + 1`)
- Timeout 120s (za Excel export velikih rasporeda)
- Logovi u `/var/log/raspored/`
- `FLASK_ENV=production` (osigurava HTTPS kolačiće)

## 4. Apache2

```bash
sudo cp deploy/apache2.conf /etc/apache2/sites-available/raspored.conf
# Uredite ServerName ako koristite drugu domenu
sudo a2ensite raspored
sudo systemctl reload apache2
```

## 5. SSL certifikat (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d raspored.foozos.hr
```

## 6. Automatski backup baze

```bash
# Kreiraj direktorij za backupove
sudo mkdir -p /var/backups/raspored
sudo chown www-data:www-data /var/backups/raspored

# Postavi dnevni backup u 3:00
sudo crontab -e
# Dodaj liniju:
# 0 3 * * * /var/www/html/FOOZOS_raspored/deploy/backup.sh >> /var/log/raspored/backup.log 2>&1
```

Skripta čuva zadnjih 30 backupova i koristi SQLite online backup (sigurno dok je baza u upotrebi).

Za ručni backup:
```bash
sudo /var/www/html/FOOZOS_raspored/deploy/backup.sh
```

Za restore:
```bash
sudo systemctl stop raspored
sudo cp /var/backups/raspored/raspored_YYYY-MM-DD_HHMM.db /var/www/html/FOOZOS_raspored/instance/raspored.db
sudo chown www-data:www-data /var/www/html/FOOZOS_raspored/instance/raspored.db
sudo systemctl start raspored
```

## 7. Provjera

```bash
sudo systemctl status raspored        # Gunicorn radi?
curl -I https://raspored.foozos.hr    # HTTPS radi?
journalctl -u raspored -f             # Logovi u realnom vremenu
tail -f /var/log/raspored/error.log   # Gunicorn greške
tail -f /var/log/raspored/access.log  # HTTP zahtjevi
```

## 8. Ažuriranje aplikacije

```bash
cd /var/www/html/FOOZOS_raspored
sudo -u www-data git pull
sudo systemctl restart raspored
```

## Napomene

- Zadana lozinka je `admin/admin` — sustav forsira promjenu pri prvoj prijavi
- Za lokalni razvoj: `FLASK_ENV=development python run.py`
- Audit logovi se čuvaju 90 dana u bazi
- Backupovi baze se čuvaju 30 dana u `/var/backups/raspored/`
