"""SHALOM Beauty Salon — Flask application factory."""

import os
from datetime import date, datetime

from flask import Flask, render_template
from flask_login import current_user

from .extensions import db, login_manager
from .models import User
from .seed import seed_database
from .utils import (
    format_currency,
    format_date_es,
    format_number,
    format_temporal_es,
    format_time_es,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False, static_url_path="")
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "shalom-development-secret-key"),
        GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY"),
        GEMINI_MODEL=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "shalom.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        REMEMBER_COOKIE_DURATION=30 * 24 * 60 * 60,
        GOOGLE_ENABLED=bool(os.environ.get("GOOGLE_CLIENT_ID")),
        GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID"),
        GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET"),
        GOOGLE_REDIRECT_URI=os.environ.get(
            "GOOGLE_REDIRECT_URI", "http://localhost:8080/login/oauth2/code/google"
        ),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = None
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # -- template helpers -------------------------------------------------
    app.jinja_env.filters["money"] = format_currency
    app.jinja_env.filters["number"] = format_number
    app.jinja_env.filters["date_es"] = format_date_es
    app.jinja_env.filters["time_es"] = format_time_es
    app.jinja_env.filters["temporal"] = format_temporal_es

    @app.context_processor
    def inject_globals():
        return {
            "google_enabled": app.config.get("GOOGLE_ENABLED", False),
            "current_year": date.today().year,
            "now": datetime.now(),
            "current_user": current_user,
            "is_admin": bool(getattr(current_user, "is_authenticated", False) and current_user.is_admin),
        }

    # -- blueprints -------------------------------------------------------
    from .routes.auth import bp as auth_bp
    from .routes.appointments import bp as appointments_bp
    from .routes.cart import bp as cart_bp
    from .routes.chatbot import bp as chatbot_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.inventory import bp as inventory_bp
    from .routes.loyalty import bp as loyalty_bp
    from .routes.misc import bp as misc_bp
    from .routes.profile import bp as profile_bp
    from .routes.preinterviews import bp as preinterviews_bp
    from .routes.reports import bp as reports_bp
    from .routes.services import bp as services_bp
    from .routes.specialists import bp as specialists_bp
    from .routes.store import bp
    from .routes.users import bp as users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(loyalty_bp)
    app.register_blueprint(misc_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(preinterviews_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(specialists_bp)
    app.register_blueprint(bp)
    app.register_blueprint(users_bp)

    with app.app_context():
        db.create_all()
        seed_database()

    return app
