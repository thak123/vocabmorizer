import os

from dotenv import load_dotenv
from flask import Flask

from .config import config
from .extensions import csrf, db, login_manager, migrate

load_dotenv()


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config["default"]))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .vocab import bp as vocab_bp
    app.register_blueprint(vocab_bp)

    from .practice import bp as practice_bp
    app.register_blueprint(practice_bp)
    # /practice/record accepts JSON so exempt from form-based CSRF
    csrf.exempt(practice_bp)

    # Ensure all models are imported so Flask-Migrate can detect them.
    from .models import user, vocabulary  # noqa: F401

    return app
