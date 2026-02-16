import os
from datetime import date
from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(os.path.dirname(app.config['DATABASE']), exist_ok=True)

    from app.db import init_app, get_db, migrate_db
    init_app(app)

    with app.app_context():
        try:
            db = get_db()
            migrate_db(db)
        except Exception:
            pass  # Baza mozda jos ne postoji

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

    @app.context_processor
    def inject_current_year():
        return {'current_year': date.today().year}

    return app
