import uuid
from datetime import date

from app.models.vocabulary import ReviewStats, VocabularyEntry


def _login(client, email="user@example.com", password="password123"):
    client.post("/auth/login", data={"email": email, "password": password})


def _add_entry(db, user_id, word="serendipity", lecture="English 101"):
    entry = VocabularyEntry(
        id=str(uuid.uuid4()),
        user_id=user_id,
        lecture=lecture,
        date_added=date.today(),
        word=word,
        synonyms=["chance", "luck"],
        antonyms=[],
        meaning="A happy accident",
        translation_en="serendipity",
        target_language="en",
    )
    stats = ReviewStats(entry_id=entry.id)
    db.session.add(entry)
    db.session.add(stats)
    db.session.commit()
    return entry


class TestVocabList:
    def test_list_requires_login(self, client):
        r = client.get("/vocab/", follow_redirects=False)
        assert r.status_code == 302

    def test_list_empty(self, client, regular_user):
        _login(client)
        r = client.get("/vocab/")
        assert r.status_code == 200
        assert b"No vocabulary entries" in r.data

    def test_list_shows_entries(self, client, db, regular_user):
        _login(client)
        _add_entry(db, regular_user.id, word="ephemeral")
        r = client.get("/vocab/")
        assert b"ephemeral" in r.data

    def test_list_lecture_filter(self, client, db, regular_user):
        _login(client)
        _add_entry(db, regular_user.id, word="alpha", lecture="Lecture A")
        _add_entry(db, regular_user.id, word="beta", lecture="Lecture B")
        r = client.get("/vocab/?lecture=Lecture+A")
        assert b"alpha" in r.data
        assert b"beta" not in r.data


class TestVocabAdd:
    def test_add_page_loads(self, client, regular_user):
        _login(client)
        r = client.get("/vocab/add")
        assert r.status_code == 200
        assert b"Add New Word" in r.data

    def test_add_creates_entry(self, client, db, regular_user):
        _login(client)
        r = client.post(
            "/vocab/add",
            data={
                "lecture": "French 101",
                "date_added": "2026-05-07",
                "word": "bonjour",
                "synonyms": "salut, coucou",
                "antonyms": "au revoir",
                "meaning": "A greeting",
                "translation_en": "hello",
                "metadata_usage": "Used as a greeting",
                "target_language": "fr",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"bonjour" in r.data
        entry = db.session.query(VocabularyEntry).filter_by(word="bonjour").first()
        assert entry is not None
        assert entry.synonyms == ["salut", "coucou"]
        assert entry.antonyms == ["au revoir"]
        assert entry.review_stats is not None

    def test_add_missing_required_fields(self, client, regular_user):
        _login(client)
        r = client.post(
            "/vocab/add",
            data={
                "lecture": "", "date_added": "2026-05-07",
                "word": "", "meaning": "", "translation_en": "",
            },
        )
        assert r.status_code == 200
        assert b"Add New Word" in r.data


class TestVocabEdit:
    def test_edit_page_loads(self, client, db, regular_user):
        _login(client)
        entry = _add_entry(db, regular_user.id)
        r = client.get(f"/vocab/{entry.id}/edit")
        assert r.status_code == 200
        assert entry.word.encode() in r.data

    def test_edit_updates_entry(self, client, db, regular_user):
        _login(client)
        entry = _add_entry(db, regular_user.id)
        r = client.post(
            f"/vocab/{entry.id}/edit",
            data={
                "lecture": "Updated Lecture",
                "date_added": "2026-05-07",
                "word": "serendipity_v2",
                "synonyms": "",
                "antonyms": "",
                "meaning": "Updated meaning",
                "translation_en": "serendipity",
                "target_language": "en",
            },
            follow_redirects=True,
        )
        assert r.status_code == 200
        db.session.expire(entry)
        assert entry.word == "serendipity_v2"
        assert entry.lecture == "Updated Lecture"

    def test_edit_other_users_entry_returns_404(self, client, db, regular_user):
        _login(client)
        other_entry = VocabularyEntry(
            id=str(uuid.uuid4()),
            user_id="other-user-id",
            lecture="X",
            date_added=date.today(),
            word="foreign",
            synonyms=[],
            antonyms=[],
            meaning="not yours",
            translation_en="foreign",
        )
        db.session.add(other_entry)
        db.session.commit()
        r = client.get(f"/vocab/{other_entry.id}/edit")
        assert r.status_code == 404


class TestVocabDelete:
    def test_delete_removes_entry(self, client, db, regular_user):
        _login(client)
        entry = _add_entry(db, regular_user.id, word="to_delete")
        entry_id = entry.id
        r = client.post(f"/vocab/{entry_id}/delete", follow_redirects=True)
        assert r.status_code == 200
        assert db.session.get(VocabularyEntry, entry_id) is None

    def test_delete_other_users_entry_returns_404(self, client, db, regular_user):
        _login(client)
        other_entry = VocabularyEntry(
            id=str(uuid.uuid4()),
            user_id="other-user-id",
            lecture="X",
            date_added=date.today(),
            word="not_yours",
            synonyms=[],
            antonyms=[],
            meaning="not yours",
            translation_en="not yours",
        )
        db.session.add(other_entry)
        db.session.commit()
        r = client.post(f"/vocab/{other_entry.id}/delete")
        assert r.status_code == 404
