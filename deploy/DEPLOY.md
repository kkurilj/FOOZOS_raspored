# Postavljanje na produkcijski server (Apache2 + Gunicorn)

## 1. Priprema servera

```bash
sudo apt update
sudo apt install apache2 python3-venv libapache2-mod-proxy-html
sudo a2enmod proxy proxy_http ssl headers rewrite
```

## 2. Aplikacija

```bash
sudo mkdir -p /var/www/raspored
sudo cp -r . /var/www/raspored/
cd /var/www/raspored
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo chown -R www-data:www-data /var/www/raspored
```

## 3. Gunicorn servis

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/raspored.service
# Uredite WorkingDirectory putanju po potrebi
sudo systemctl daemon-reload
sudo systemctl enable raspored
sudo systemctl start raspored
```

## 4. Apache2

```bash
sudo cp deploy/apache2.conf /etc/apache2/sites-available/raspored.conf
# Uredite ServerName i SSL putanje
sudo a2ensite raspored
sudo systemctl reload apache2
```

## 5. SSL certifikat (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-apache
sudo certbot --apache -d raspored.example.com
```

## 6. Provjera

```bash
sudo systemctl status raspored     # Gunicorn radi?
curl -I https://raspored.example.com  # HTTPS radi?
```

## Napomene

- Zadana lozinka je `admin/admin` — sustav forsira promjenu pri prvoj prijavi
- Za lokalni razvoj: `FLASK_ENV=development python run.py`
- Logovi: `journalctl -u raspored -f`
