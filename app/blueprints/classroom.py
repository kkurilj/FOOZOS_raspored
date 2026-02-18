from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db
from app.auth import login_required
from app.audit import log_audit

bp = Blueprint('classroom', __name__)


@bp.route('/')
@login_required
def index():
    db = get_db()
    classrooms = db.execute('SELECT * FROM classroom ORDER BY name').fetchall()
    return render_template('classroom/index.html', classrooms=classrooms)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Naziv učionice je obavezan.', 'danger')
        else:
            db = get_db()
            try:
                cursor = db.execute('INSERT INTO classroom (name) VALUES (?)', (name,))
                log_audit('create', 'classroom', f'Dodana učionica "{name}"', cursor.lastrowid, db)
                db.commit()
                flash(f'Učionica "{name}" je dodana.', 'success')
                return redirect(url_for('classroom.index'))
            except db.IntegrityError:
                flash(f'Učionica "{name}" već postoji.', 'danger')
    return render_template('classroom/form.html')


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    db = get_db()
    classroom = db.execute('SELECT * FROM classroom WHERE id = ?', (id,)).fetchone()
    if classroom is None:
        flash('Učionica nije pronađena.', 'danger')
        return redirect(url_for('classroom.index'))

    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Naziv učionice je obavezan.', 'danger')
        else:
            try:
                db.execute('UPDATE classroom SET name = ? WHERE id = ?', (name, id))
                log_audit('update', 'classroom', f'Ažurirana učionica "{classroom["name"]}" → "{name}"', id, db)
                db.commit()
                flash('Učionica je ažurirana.', 'success')
                return redirect(url_for('classroom.index'))
            except db.IntegrityError:
                flash(f'Učionica "{name}" već postoji.', 'danger')
    return render_template('classroom/form.html', classroom=classroom)


@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    db = get_db()
    cl = db.execute('SELECT name FROM classroom WHERE id = ?', (id,)).fetchone()
    log_audit('delete', 'classroom', f'Obrisana učionica "{cl["name"]}"' if cl else f'Obrisana učionica ID={id}', id, db)
    db.execute('DELETE FROM classroom WHERE id = ?', (id,))
    db.commit()
    flash('Učionica je obrisana.', 'success')
    return redirect(url_for('classroom.index'))
