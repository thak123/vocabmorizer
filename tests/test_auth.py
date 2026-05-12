from app.models.user import User


class TestLogin:
    def test_login_page_loads(self, client):
        r = client.get("/auth/login")
        assert r.status_code == 200
        assert b"Sign In" in r.data

    def test_login_with_valid_credentials(self, client, regular_user):
        r = client.post(
            "/auth/login",
            data={"email": "user@example.com", "password": "password123"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"Welcome" in r.data

    def test_login_with_wrong_password(self, client, regular_user):
        r = client.post(
            "/auth/login",
            data={"email": "user@example.com", "password": "wrongpassword"},
            follow_redirects=True,
        )
        assert b"Invalid email or password" in r.data

    def test_login_admin_bootstrap(self, client):
        r = client.post(
            "/auth/login",
            data={"email": "admin", "password": "test-admin-pw"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"Welcome" in r.data

    def test_login_admin_wrong_password(self, client):
        r = client.post(
            "/auth/login",
            data={"email": "admin", "password": "wrongpw"},
        )
        assert r.status_code == 200
        assert b"Invalid email or password" in r.data

    def test_logout_redirects_to_login(self, client, regular_user):
        client.post(
            "/auth/login",
            data={"email": "user@example.com", "password": "password123"},
        )
        r = client.get("/auth/logout", follow_redirects=True)
        assert r.status_code == 200
        assert b"Sign In" in r.data


class TestRegister:
    def test_register_page_loads(self, client):
        r = client.get("/auth/register")
        assert r.status_code == 200
        assert b"Create Account" in r.data

    def test_register_new_user(self, client, db):
        r = client.post(
            "/auth/register",
            data={
                "name": "New Person",
                "email": "new@example.com",
                "password": "securepass1",
                "password2": "securepass1",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"Account created" in r.data
        assert db.session.query(User).filter_by(email="new@example.com").first() is not None

    def test_register_duplicate_email(self, client, regular_user):
        r = client.post(
            "/auth/register",
            data={
                "name": "Dupe",
                "email": "user@example.com",
                "password": "securepass1",
                "password2": "securepass1",
            },
            follow_redirects=True,
        )
        assert b"already exists" in r.data

    def test_register_password_mismatch(self, client):
        r = client.post(
            "/auth/register",
            data={
                "name": "Someone",
                "email": "someone@example.com",
                "password": "securepass1",
                "password2": "differentpass",
            },
        )
        assert r.status_code == 200
        assert b"Create Account" in r.data
