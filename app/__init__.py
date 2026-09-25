from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config

db = SQLAlchemy()
csrf = CSRFProtect()


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.inquilinos import inquilinos_bp


    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inquilinos_bp)

    @app.route("/test-db")
    def test_db():
        from sqlalchemy import text

        try:
            db.session.execute(text("SELECT 1"))
            return "Conexión a PostgreSQL exitosa."
        except Exception as e:
            return f"Error de conexión: {e}"

    return app