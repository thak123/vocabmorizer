import uuid
from datetime import datetime, timezone

import bcrypt
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models.user import User
from . import bp
from .forms import LoginForm, RegisterForm

ADMIN_USERNAME = "admin"


def _check_admin_password(password: str) -> bool:
    admin_pw = current_app.config.get("ADMIN_PASSWORD", "")
    return bool(admin_pw) and password == admin_pw


class _AdminProxy:
    """Minimal UserMixin-compatible object for the env-var admin account."""

    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self) -> None:
        self.id = "admin"
        self.name = "Admin"
        self.email = "admin@local"
        self.role = "admin"
        self.preferred_language = "en"

    def get_id(self) -> str:
        return "admin"

    def is_admin(self) -> bool:
        return True


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email_or_user = form.email.data.strip()
        password = form.password.data

        # Admin bootstrap account — checked before touching the DB.
        if email_or_user.lower() == ADMIN_USERNAME and _check_admin_password(password):
            proxy = _AdminProxy()
            login_user(proxy, remember=form.remember_me.data)  # type: ignore[arg-type]
            return redirect(request.args.get("next") or url_for("auth.index"))

        user = User.query.filter_by(email=email_or_user).first()
        if user and user.password_hash and bcrypt.checkpw(
            password.encode(), user.password_hash.encode()
        ):
            user.last_active = datetime.now(timezone.utc)
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            return redirect(request.args.get("next") or url_for("auth.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.strip()).first():
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html", form=form)

        pw_hash = bcrypt.hashpw(form.password.data.encode(), bcrypt.gensalt()).decode()
        user = User(
            id=str(uuid.uuid4()),
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            password_hash=pw_hash,
            auth_provider="local",
            role="user",
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/")
@login_required
def index():
    return render_template("home.html")


@bp.route("/set-locale/<code>")
def set_locale(code: str):
    from flask import session

    from app import SUPPORTED_LOCALES

    if code in SUPPORTED_LOCALES:
        session["locale"] = code
        if current_user.is_authenticated and hasattr(current_user, "preferred_language"):
            current_user.preferred_language = code
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

    return redirect(request.referrer or url_for("auth.index"))
