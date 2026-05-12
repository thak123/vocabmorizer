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
        synonyms=[],
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


class TestPracticeSetup:
    def test_setup_requires_login(self, client):
        r = client.get("/practice/", follow_redirects=False)
        assert r.status_code == 302

    def test_setup_page_loads(self, client, regular_user):
        _login(client)
        r = client.get("/practice/")
        assert r.status_code == 200
        assert b"Practice" in r.data

    def test_start_with_no_entries_flashes_warning(self, client, regular_user):
        _login(client)
        r = client.post(
            "/practice/start",
            data={"mode": "all"},
            follow_redirects=True,
        )
        assert b"No vocabulary" in r.data

    def test_start_creates_session_and_redirects_to_card(self, client, db, regular_user):
        _login(client)
        _add_entry(db, regular_user.id)
        r = client.post("/practice/start", data={"mode": "all"}, follow_redirects=False)
        assert r.status_code == 302
        assert "/practice/card" in r.headers["Location"]


class TestPracticeCard:
    def test_card_without_session_redirects_to_setup(self, client, regular_user):
        _login(client)
        r = client.get("/practice/card", follow_redirects=False)
        assert r.status_code == 302
        assert "/practice/" in r.headers["Location"]

    def test_card_shows_entry(self, client, db, regular_user):
        _login(client)
        _add_entry(db, regular_user.id, word="ephemeral")
        client.post("/practice/start", data={"mode": "all"})
        r = client.get("/practice/card")
        assert r.status_code == 200
        assert b"ephemeral" in r.data


class TestPracticeRecord:
    def test_record_correct_updates_stats(self, client, db, regular_user):
        _login(client)
        entry = _add_entry(db, regular_user.id)
        client.post("/practice/start", data={"mode": "all"})

        r = client.post(
            "/practice/record",
            json={"entry_id": entry.id, "result": "correct"},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert "next" in data

        db.session.expire(entry.review_stats)
        assert entry.review_stats.times_reviewed == 1
        assert entry.review_stats.correct_count == 1
        assert entry.review_stats.consecutive_correct == 1

    def test_record_incorrect_flags_problematic_after_threshold(self, client, db, regular_user):
        _login(client)
        entry = _add_entry(db, regular_user.id)
        # Seed stats to be just below threshold (2/5 incorrect = 40%)
        entry.review_stats.times_reviewed = 4
        entry.review_stats.correct_count = 3
        entry.review_stats.consecutive_correct = 0
        db.session.commit()

        client.post("/practice/start", data={"mode": "all"})
        client.post("/practice/record", json={"entry_id": entry.id, "result": "incorrect"})

        db.session.expire(entry.review_stats)
        assert entry.review_stats.is_problematic is True

    def test_record_invalid_result_returns_400(self, client, db, regular_user):
        _login(client)
        _add_entry(db, regular_user.id)
        client.post("/practice/start", data={"mode": "all"})
        r = client.post("/practice/record", json={"entry_id": "x", "result": "maybe"})
        assert r.status_code == 400

    def test_record_without_session_returns_400(self, client, regular_user):
        _login(client)
        r = client.post("/practice/record", json={"entry_id": "x", "result": "correct"})
        assert r.status_code == 400


class TestPracticeDone:
    def test_done_page_shows_summary(self, client, db, regular_user):
        _login(client)
        entry = _add_entry(db, regular_user.id)
        client.post("/practice/start", data={"mode": "all"})
        client.post("/practice/record", json={"entry_id": entry.id, "result": "correct"})
        r = client.get("/practice/done")
        assert r.status_code == 200
        assert b"complete" in r.data

    def test_done_clears_session(self, client, db, regular_user):
        _login(client)
        _add_entry(db, regular_user.id)
        client.post("/practice/start", data={"mode": "all"})
        client.get("/practice/done")
        # After done, /practice/card should redirect back to setup
        r = client.get("/practice/card", follow_redirects=False)
        assert "/practice/" in r.headers["Location"]
