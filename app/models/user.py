import uuid
from datetime import datetime, timezone

from flask_login import UserMixin

from ..extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    role = db.Column(db.String(16), nullable=False, default="user")  # "user" | "admin"
    auth_provider = db.Column(db.String(16), nullable=False, default="local")  # "local" | "google"
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)
    preferred_language = db.Column(db.String(8), nullable=False, default="en")
    date_joined = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_active = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, user_id)
