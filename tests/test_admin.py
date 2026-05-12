import uuid

from app.models.user import User


def _login(client, email="user@example.com", password="password123"):
    client.post("/auth/login", data={"email": email, "password": password})


def _login_admin(client):
    client.post("/auth/login", data={"email": "admin", "password": "test-admin-pw"})


def _make_admin_user(db):
    """Create a real admin user in the DB."""
    import bcrypt
    pw = bcrypt.hashpw(b"adminpass", bcrypt.gensalt()).decode()
    u = User(
        id=str(uuid.uuid4()),
        name="DB Admin",
        email="dbadmin@example.com",
        role="admin",
        auth_provider="local",
        password_hash=pw,
    )
    db.session.add(u)
    db.session.commit()
    return u


class TestAdminAccess:
    def test_panel_requires_login(self, client):
        r = client.get("/admin/", follow_redirects=False)
        assert r.status_code == 302

    def test_panel_blocked_for_regular_user(self, client, regular_user):
        _login(client)
        r = client.get("/admin/")
        assert r.status_code == 403

    def test_panel_accessible_to_bootstrap_admin(self, client):
        _login_admin(client)
        r = client.get("/admin/")
        assert r.status_code == 200
        assert b"Admin Panel" in r.data

    def test_panel_accessible_to_db_admin(self, client, db):
        _make_admin_user(db)
        client.post("/auth/login", data={"email": "dbadmin@example.com", "password": "adminpass"})
        r = client.get("/admin/")
        assert r.status_code == 200


class TestAdminCreateUser:
    def test_create_user(self, client, db):
        _login_admin(client)
        r = client.post(
            "/admin/users/create",
            data={"name": "New Person", "email": "admin-created@example.com",
                  "password": "pass1234", "role": "user"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"created" in r.data
        created = db.session.query(User).filter_by(email="admin-created@example.com").first()
        assert created is not None

    def test_create_duplicate_email_fails(self, client, db, regular_user):
        _login_admin(client)
        r = client.post(
            "/admin/users/create",
            data={"name": "Dup", "email": "user@example.com",
                  "password": "pass1234", "role": "user"},
            follow_redirects=True,
        )
        assert b"already exists" in r.data

    def test_create_user_missing_fields(self, client, db):
        _login_admin(client)
        r = client.post(
            "/admin/users/create",
            data={"name": "", "email": "", "password": "", "role": "user"},
            follow_redirects=True,
        )
        assert b"required" in r.data


class TestAdminDeleteUser:
    def test_delete_user_removes_account(self, client, db, regular_user):
        _login_admin(client)
        user_id = regular_user.id
        r = client.post(f"/admin/users/{user_id}/delete", follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(User, user_id) is None

    def test_delete_nonexistent_user(self, client):
        _login_admin(client)
        r = client.post("/admin/users/nonexistent-id/delete", follow_redirects=True)
        assert b"not found" in r.data


class TestAdminPromoteDemote:
    def test_promote_user_to_admin(self, client, db, regular_user):
        _login_admin(client)
        client.post(f"/admin/users/{regular_user.id}/promote")
        db.session.expire(regular_user)
        assert regular_user.role == "admin"

    def test_demote_admin_to_user(self, client, db, regular_user):
        _login_admin(client)
        regular_user.role = "admin"
        db.session.commit()
        client.post(f"/admin/users/{regular_user.id}/demote")
        db.session.expire(regular_user)
        assert regular_user.role == "user"
