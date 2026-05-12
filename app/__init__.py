import os

from dotenv import load_dotenv
from flask import Flask

from .config import config
from .extensions import babel, csrf, db, login_manager, migrate

load_dotenv()

SUPPORTED_LOCALES = ["en", "hr", "es", "pl", "uk"]


def _get_locale():
    from flask import request, session
    from flask_login import current_user

    # 1. Authenticated user's saved preference
    if current_user.is_authenticated and hasattr(current_user, "preferred_language"):
        lang = current_user.preferred_language
        if lang in SUPPORTED_LOCALES:
            return lang

    # 2. Session cookie (set by language switcher for anonymous users)
    lang = session.get("locale")
    if lang in SUPPORTED_LOCALES:
        return lang

    # 3. Browser Accept-Language header
    return request.accept_languages.best_match(SUPPORTED_LOCALES, default="en")


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
        static_url_path="/static",
    )
    app.config.from_object(config.get(config_name, config["default"]))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    babel.init_app(app, locale_selector=_get_locale)

    # Flask-Babel 4.x no longer injects get_locale() into templates automatically
    from flask_babel import get_locale
    app.jinja_env.globals["get_locale"] = get_locale

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .vocab import bp as vocab_bp
    app.register_blueprint(vocab_bp)

    from .practice import bp as practice_bp
    app.register_blueprint(practice_bp)
    # /practice/record accepts JSON so exempt from form-based CSRF
    csrf.exempt(practice_bp)

    from .admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    from .io import bp as io_bp
    app.register_blueprint(io_bp)

    # Ensure all models are imported so Flask-Migrate can detect them.
    from .models import user, vocabulary  # noqa: F401

    return app
