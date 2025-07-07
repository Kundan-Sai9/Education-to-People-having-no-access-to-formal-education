from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(
        __name__,
        static_url_path='/static',
        static_folder='../static'
    )

    # Use absolute path to the database
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, '..', 'database', 'edulink.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

    app.config['SECRET_KEY'] = 'supersecretkey'

    db.init_app(app)

    from .routes import auth, student, volunteer
    app.register_blueprint(auth.bp)
    app.register_blueprint(student.student_bp)
    app.register_blueprint(volunteer.bp)

    return app
