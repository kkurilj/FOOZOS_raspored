import os
from datetime import date
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Podrška za reverse proxy (Apache2 mod_proxy) - ispravno čita IP adresu klijenta
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

    from app.db import init_app, get_db, migrate_db
    init_app(app)

    with app.app_context():
        try:
            db = get_db()
            migrate_db(db)
        except Exception as e:
            app.logger.warning('Migracija baze nije uspjela: %s', e)

    from app.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.academic_year import bp as academic_year_bp
    app.register_blueprint(academic_year_bp, url_prefix='/academic-year')

    from app.blueprints.study_program import bp as study_program_bp
    app.register_blueprint(study_program_bp, url_prefix='/study-program')

    from app.blueprints.professor import bp as professor_bp
    app.register_blueprint(professor_bp, url_prefix='/professor')

    from app.blueprints.classroom import bp as classroom_bp
    app.register_blueprint(classroom_bp, url_prefix='/classroom')

    from app.blueprints.course import bp as course_bp
    app.register_blueprint(course_bp, url_prefix='/course')

    from app.blueprints.schedule import bp as schedule_bp
    app.register_blueprint(schedule_bp, url_prefix='/schedule')

    from app.blueprints.timetable import bp as timetable_bp
    app.register_blueprint(timetable_bp, url_prefix='/timetable')

    from app.blueprints.day_status import bp as day_status_bp
    app.register_blueprint(day_status_bp, url_prefix='/day-status')

    from app.blueprints.database import bp as database_bp
    app.register_blueprint(database_bp, url_prefix='/database')

    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from app.blueprints.audit_log import bp as audit_log_bp
    app.register_blueprint(audit_log_bp, url_prefix='/audit-log')

    from app.blueprints.analytics import bp as analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    # CSRF zaštita
    from app.csrf import validate_csrf, generate_csrf_token, csrf_input

    @app.before_request
    def refresh_session():
        from flask import session
        if 'user_id' in session:
            session.modified = True

    @app.before_request
    def csrf_protect():
        validate_csrf()

    @app.after_request
    def track_visit(response):
        """Bilježi posjete stranica u bazu za analitiku."""
        try:
            from flask import request as req, session
            # Preskoči: statičke datoteke, API, health, ne-GET, ne-HTML
            path = req.path
            if (req.method != 'GET'
                    or path.startswith('/static/')
                    or '/api/' in path
                    or path == '/health'
                    or response.status_code >= 400
                    or 'text/html' not in (response.content_type or '')):
                return response
            from app.blueprints.analytics import parse_user_agent
            ua = req.headers.get('User-Agent', '')
            device_type, browser, os_name = parse_user_agent(ua)
            db = get_db()
            db.execute(
                '''INSERT INTO page_visit (path, ip_address, user_agent, device_type, browser, os, is_admin)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (path, req.remote_addr or '', ua, device_type, browser, os_name,
                 1 if 'user_id' in session else 0)
            )
            db.commit()
        except Exception:
            pass  # Ne blokiraj korisnika ako tracking zakaže
        return response

    @app.context_processor
    def inject_globals():
        from app.auth import is_admin, is_super_admin
        from flask import session
        conflict_count = 0
        unpublished_count = 0
        if is_admin():
            try:
                from app.db import get_db as _get_db
                _db = _get_db()
                conflict_count = _db.execute(
                    'SELECT COUNT(*) FROM schedule_entry WHERE has_conflict = 1'
                ).fetchone()[0]
                unpublished_count = _db.execute(
                    'SELECT COUNT(*) FROM schedule_entry WHERE is_published = 0'
                ).fetchone()[0]
            except Exception:
                pass
        return {
            'current_year': date.today().year,
            'is_admin': is_admin(),
            'is_super_admin': is_super_admin(),
            'current_user_display_name': session.get('user_display_name', ''),
            'csrf_token': generate_csrf_token(),
            'csrf_input': csrf_input(),
            'conflict_count': conflict_count,
            'unpublished_count': unpublished_count,
        }

    # Custom error handleri - ne prikazuj stack trace
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error('500 Internal Server Error: %s', e, exc_info=True)
        return render_template('errors/500.html'), 500

    # Sigurnosni HTTP headeri
    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    return app
