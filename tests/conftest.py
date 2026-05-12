import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db as _db
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    test_app = create_app("testing")
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        # StaticPool shares one in-memory connection across all app contexts,
        # so fixtures and test-client requests see the same data.
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
        ADMIN_PASSWORD="test-admin-pw",
        SECRET_KEY="test-secret",
    )
    # Create tables once, then yield without holding an app context open.
    # Holding a session-scoped app context would share `g` across all
    # requests, leaking Flask-Login's `g._login_user` between tests.
    with test_app.app_context():
        _db.create_all()
    yield test_app
    with test_app.app_context():
        _db.drop_all()


@pytest.fixture()
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture()
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture()
def regular_user(db):
    import bcrypt

    pw_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
    user = User(
        name="Test User",
        email="user@example.com",
        password_hash=pw_hash,
        auth_provider="local",
        role="user",
    )
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()
