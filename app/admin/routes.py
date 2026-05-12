import uuid

import bcrypt
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..extensions import db
from ..models.user import User
from ..utils.decorators import admin_required
from . import bp


@bp.route("/")
@login_required
@admin_required
def panel():
    users = User.query.order_by(User.date_joined.desc()).all()
    return render_template("admin/panel.html", users=users)


@bp.route("/users/create", methods=["POST"])
@login_required
@admin_required
def create_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    role = request.form.get("role", "user")
    password = request.form.get("password", "").strip()

    if not name or not email or not password:
        flash("Name, email and password are required.", "danger")
        return redirect(url_for("admin.panel"))

    if role not in ("user", "admin"):
        role = "user"

    if User.query.filter_by(email=email).first():
        flash(f"An account with email {email} already exists.", "danger")
        return redirect(url_for("admin.panel"))

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        role=role,
        auth_provider="local",
        password_hash=pw_hash,
    )
    db.session.add(user)
    db.session.commit()
    flash(f"User '{name}' created.", "success")
    return redirect(url_for("admin.panel"))


@bp.route("/users/<user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id: str):
    user = db.session.get(User, user_id)
    if user is None:
        flash("User not found.", "danger")
        return redirect(url_for("admin.panel"))

    name = user.name
    # Vocabulary entries cascade-delete via the relationship in User model.
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{name}' and all their data deleted.", "info")
    return redirect(url_for("admin.panel"))


@bp.route("/users/<user_id>/promote", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id: str):
    user = db.session.get(User, user_id)
    if user:
        user.role = "admin"
        db.session.commit()
        flash(f"'{user.name}' promoted to admin.", "success")
    return redirect(url_for("admin.panel"))


@bp.route("/users/<user_id>/demote", methods=["POST"])
@login_required
@admin_required
def demote_user(user_id: str):
    user = db.session.get(User, user_id)
    if user:
        user.role = "user"
        db.session.commit()
        flash(f"'{user.name}' demoted to user.", "info")
    return redirect(url_for("admin.panel"))
