from flask import Flask
from .extensions import db, login_manager
from .routes import auth_bp, stats_bp


def create_app():
    app = Flask(__name__)

    # ── Config ──────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = "change-me-in-production"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://USER:PASSWORD@localhost:3306/gympal"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Extensions ──────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"   # redirect here if @login_required fails

    # Tells Flask-Login how to reload a user from the session cookie
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ──────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(stats_bp)

    # ── DB init (dev only – use Flask-Migrate in production) ────────────────
    with app.app_context():
        db.create_all()

    return app
