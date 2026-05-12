"""Tests for the import/export blueprint (/io)."""
import io
import json
import uuid

import pytest

from app.models.vocabulary import VocabularyEntry
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, email="user@example.com", password="password123"):
    client.post("/auth/login", data={"email": email, "password": password})


def _make_user(db, email="io_user@example.com"):
    import bcrypt
    pw = bcrypt.hashpw(b"pw1234", bcrypt.gensalt()).decode()
    u = User(
        id=str(uuid.uuid4()),
        name="IO User",
        email=email,
        role="user",
        auth_provider="local",
        password_hash=pw,
    )
    db.session.add(u)
    db.session.commit()
    return u


def _make_entry(db, user_id, word="hello", lecture="Unit1", target_language="hr"):
    from datetime import date
    e = VocabularyEntry(
        id=str(uuid.uuid4()),
        user_id=user_id,
        word=word,
        lecture=lecture,
        date_added=date.today(),
        meaning="greeting",
        translation_en="hello",
        target_language=target_language,
        synonyms=[],
        antonyms=[],
    )
    db.session.add(e)
    db.session.commit()
    return e


# ---------------------------------------------------------------------------
# Exporters (unit-level)
# ---------------------------------------------------------------------------

class TestExporters:
    def test_export_csv_returns_bom(self, db, app):
        with app.app_context():
            from app.io.exporters import export_csv
            from app.models.vocabulary import VocabularyEntry as VE
            entries = []
            result = export_csv(entries)
            assert result.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM

    def test_export_csv_has_header(self, db, app):
        with app.app_context():
            from app.io.exporters import export_csv
            result = export_csv([]).decode("utf-8-sig")
            assert "word" in result
            assert "meaning" in result

    def test_export_tsv_uses_tab_delimiter(self, db, app):
        with app.app_context():
            from app.io.exporters import export_tsv
            result = export_tsv([]).decode("utf-8")
            header_line = result.splitlines()[0]
            assert "\t" in header_line

    def test_export_json_empty(self, db, app):
        with app.app_context():
            from app.io.exporters import export_json
            result = json.loads(export_json([]))
            assert result == []

    def test_export_excel_returns_xlsx_magic(self, db, app):
        with app.app_context():
            from app.io.exporters import export_excel
            result = export_excel([])
            # XLSX is a ZIP file — starts with PK magic bytes
            assert result[:2] == b"PK"


# ---------------------------------------------------------------------------
# Importers (unit-level)
# ---------------------------------------------------------------------------

class TestParsers:
    def test_parse_csv(self, app):
        with app.app_context():
            from app.io.importers import parse_file
            csv_bytes = b"word,meaning,target_language\nhello,greeting,hr\n"
            rows, errors = parse_file("words.csv", csv_bytes)
            assert not errors
            assert len(rows) == 1
            assert rows[0]["word"] == "hello"

    def test_parse_tsv(self, app):
        with app.app_context():
            from app.io.importers import parse_file
            tsv_bytes = b"word\tmeaning\ttarget_language\nworld\tuniverse\thr\n"
            rows, errors = parse_file("words.tsv", tsv_bytes)
            assert not errors
            assert rows[0]["word"] == "world"

    def test_parse_json(self, app):
        with app.app_context():
            from app.io.importers import parse_file
            payload = json.dumps([
                {"word": "test", "meaning": "a test", "target_language": "hr"}
            ]).encode()
            rows, errors = parse_file("words.json", payload)
            assert not errors
            assert rows[0]["word"] == "test"

    def test_parse_unknown_extension(self, app):
        with app.app_context():
            from app.io.importers import parse_file
            rows, errors = parse_file("words.txt", b"")
            assert rows == []
            assert errors

    def test_parse_bom_csv(self, app):
        with app.app_context():
            from app.io.importers import parse_file
            csv_bytes = ("﻿word,meaning,target_language\nhola,hello,es\n").encode("utf-8")
            rows, errors = parse_file("words.csv", csv_bytes)
            assert not errors
            assert rows[0]["word"] == "hola"


class TestValidateRows:
    def test_missing_required_fields(self, db, app):
        with app.app_context():
            from app.io.importers import validate_rows
            user = _make_user(db, email=f"vr_{uuid.uuid4().hex[:6]}@x.com")
            rows = [{"word": "hi", "meaning": ""}]  # target_language missing
            valid, dups, errors = validate_rows(rows, user.id)
            assert len(errors) == 1
            assert valid == []

    def test_duplicate_detection(self, db, app):
        with app.app_context():
            from app.io.importers import validate_rows
            user = _make_user(db, email=f"dup_{uuid.uuid4().hex[:6]}@x.com")
            _make_entry(db, user.id, word="hello", lecture="Unit1")
            rows = [{"word": "hello", "lecture": "Unit1",
                     "meaning": "greeting", "target_language": "hr"}]
            valid, dups, errors = validate_rows(rows, user.id)
            assert len(dups) == 1
            assert valid == []

    def test_valid_row_passes(self, db, app):
        with app.app_context():
            from app.io.importers import validate_rows
            user = _make_user(db, email=f"vp_{uuid.uuid4().hex[:6]}@x.com")
            rows = [{"word": "new_word", "meaning": "brand new",
                     "target_language": "hr", "lecture": "U1"}]
            valid, dups, errors = validate_rows(rows, user.id)
            assert len(valid) == 1
            assert dups == []
            assert errors == []


class TestCommitImport:
    def test_import_inserts_entries(self, db, app):
        with app.app_context():
            from app.io.importers import commit_import
            user = _make_user(db, email=f"ci_{uuid.uuid4().hex[:6]}@x.com")
            rows = [{"word": "imported_word", "meaning": "some meaning",
                     "target_language": "hr", "lecture": "Lec1"}]
            count = commit_import(rows, user.id)
            assert count == 1
            e = VocabularyEntry.query.filter_by(
                word="imported_word", user_id=user.id).first()
            assert e is not None
            assert e.lecture == "Lec1"

    def test_overwrite_updates_entry(self, db, app):
        with app.app_context():
            from app.io.importers import commit_import
            user = _make_user(db, email=f"ow_{uuid.uuid4().hex[:6]}@x.com")
            _make_entry(db, user.id, word="hello", lecture="Unit1")
            rows = [{"word": "hello", "lecture": "Unit1",
                     "meaning": "updated meaning", "target_language": "hr"}]
            count = commit_import(rows, user.id, overwrite=True)
            assert count == 1
            e = VocabularyEntry.query.filter_by(
                word="hello", user_id=user.id).first()
            assert e.meaning == "updated meaning"


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------

class TestExportRoute:
    def test_export_requires_login(self, client):
        r = client.get("/io/export?format=csv", follow_redirects=False)
        assert r.status_code == 302

    def test_export_csv(self, client, db):
        user = _make_user(db, email=f"ex_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        _make_entry(db, user.id, word="exported")
        r = client.get("/io/export?format=csv")
        assert r.status_code == 200
        assert b"exported" in r.data
        assert r.content_type.startswith("text/csv")

    def test_export_json(self, client, db):
        user = _make_user(db, email=f"ej_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        _make_entry(db, user.id, word="jsonword")
        r = client.get("/io/export?format=json")
        assert r.status_code == 200
        payload = json.loads(r.data)
        words = [row["word"] for row in payload]
        assert "jsonword" in words

    def test_export_invalid_format(self, client, db):
        user = _make_user(db, email=f"ef_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        r = client.get("/io/export?format=xml", follow_redirects=True)
        assert b"Invalid" in r.data

    def test_export_filters_by_lecture(self, client, db):
        user = _make_user(db, email=f"el_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        _make_entry(db, user.id, word="word_a", lecture="LecA")
        _make_entry(db, user.id, word="word_b", lecture="LecB")
        r = client.get("/io/export?format=csv&lecture=LecA")
        assert b"word_a" in r.data
        assert b"word_b" not in r.data


class TestImportRoute:
    def test_import_page_requires_login(self, client):
        r = client.get("/io/import", follow_redirects=False)
        assert r.status_code == 302

    def test_import_page_loads(self, client, db):
        user = _make_user(db, email=f"ip_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        r = client.get("/io/import")
        assert r.status_code == 200
        assert b"Import" in r.data

    def test_import_no_file_shows_error(self, client, db):
        user = _make_user(db, email=f"inf_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        r = client.post("/io/import", data={}, follow_redirects=True)
        assert b"choose" in r.data.lower()

    def test_import_csv_reaches_preview(self, client, db):
        user = _make_user(db, email=f"icp_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        csv_bytes = b"word,meaning,target_language,lecture\nhola,hello,es,Unit1\n"
        r = client.post(
            "/io/import",
            data={"file": (io.BytesIO(csv_bytes), "words.csv")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"Preview" in r.data

    def test_import_confirm_inserts(self, client, db):
        user = _make_user(db, email=f"ici_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        csv_bytes = b"word,meaning,target_language,lecture\nbonsoir,good evening,fr,Unit1\n"
        # Upload
        client.post(
            "/io/import",
            data={"file": (io.BytesIO(csv_bytes), "words.csv")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        # Confirm
        with db.session.no_autoflush:
            r = client.post("/io/import/confirm", data={}, follow_redirects=True)
        assert b"imported" in r.data.lower()
        with db.engine.connect() as conn:
            pass  # just verify no exception
        e = VocabularyEntry.query.filter_by(word="bonsoir", user_id=user.id).first()
        assert e is not None

    def test_cancel_import(self, client, db):
        user = _make_user(db, email=f"ica_{uuid.uuid4().hex[:6]}@x.com")
        _login(client, user.email, "pw1234")
        r = client.get("/io/import/cancel", follow_redirects=True)
        assert r.status_code == 200
