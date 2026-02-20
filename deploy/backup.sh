#!/bin/bash
# Dnevni backup SQLite baze podataka
# Postaviti kao cron job: sudo crontab -e
# 0 3 * * * /var/www/raspored/deploy/backup.sh
#
# Cuva zadnjih 30 backupova (30 dana)

BACKUP_DIR="/var/backups/raspored"
DB_PATH="/var/www/raspored/instance/raspored.db"
DATE=$(date +%Y-%m-%d_%H%M)
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

# SQLite online backup (sigurno i dok je baza u upotrebi)
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/raspored_$DATE.db'"

if [ $? -eq 0 ]; then
    echo "$(date): Backup uspjesan -> raspored_$DATE.db"
else
    echo "$(date): GRESKA pri backupu!" >&2
    exit 1
fi

# Obrisi backupove starije od KEEP_DAYS dana
find "$BACKUP_DIR" -name "raspored_*.db" -mtime +$KEEP_DAYS -delete
