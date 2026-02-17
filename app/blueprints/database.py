import os
import shutil
import sqlite3
import tempfile
from flask import Blueprint, render_template, current_app, send_file, request, flash, redirect, url_for, g
from app.auth import login_required

bp = Blueprint('database', __name__)


@bp.route('/')
@login_required
def index():
    db_path = current_app.config['DATABASE']
    db_exists = os.path.exists(db_path)
    db_size = os.path.getsize(db_path) if db_exists else 0
    return render_template('database/index.html', db_exists=db_exists, db_size=db_size)


@bp.route('/export')
@login_required
def export():
    db_path = current_app.config['DATABASE']
    if not os.path.exists(db_path):
        flash('Baza podataka ne postoji.', 'danger')
        return redirect(url_for('database.index'))

    # Close current connection before sending file
    db = g.pop('db', None)
    if db is not None:
        db.close()

    return send_file(
        db_path,
        as_attachment=True,
        download_name='raspored.db'
    )


@bp.route('/import', methods=['POST'])
@login_required
def import_db():
    if 'db_file' not in request.files:
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('database.index'))

    file = request.files['db_file']
    if file.filename == '':
        flash('Datoteka nije odabrana.', 'danger')
        return redirect(url_for('database.index'))

    # Save uploaded file to a temporary location
    fd, tmp_path = tempfile.mkstemp(suffix='.db')
    try:
        os.close(fd)
        file.save(tmp_path)

        # Validate it's a valid SQLite database
        try:
            conn = sqlite3.connect(tmp_path)
            result = conn.execute('PRAGMA integrity_check').fetchone()
            conn.close()
            if result[0] != 'ok':
                flash('Datoteka nije ispravna SQLite baza podataka.', 'danger')
                return redirect(url_for('database.index'))
        except Exception:
            flash('Datoteka nije ispravna SQLite baza podataka.', 'danger')
            return redirect(url_for('database.index'))

        # Close current database connection
        db = g.pop('db', None)
        if db is not None:
            db.close()

        # Replace current database
        db_path = current_app.config['DATABASE']
        shutil.copy2(tmp_path, db_path)

        flash('Baza podataka je uspješno uvezena.', 'success')
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return redirect(url_for('database.index'))
