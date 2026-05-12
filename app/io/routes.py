"""Import / export routes for /io."""
from __future__ import annotations

from flask import flash, redirect, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required

import io

from . import bp
from .exporters import export_csv, export_excel, export_json, export_tsv
from .importers import (
    commit_import,
    delete_pending,
    load_pending,
    parse_file,
    save_pending,
    validate_rows,
)
from ..models.vocabulary import VocabularyEntry

_MIME = {
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "json": "application/json",
}

_EXPORTERS = {
    "csv": export_csv,
    "tsv": export_tsv,
    "xlsx": export_excel,
    "json": export_json,
}


@bp.route("/export")
@login_required
def export():
    fmt = request.args.get("format", "csv").lower()
    lecture = request.args.get("lecture", "").strip()

    if fmt not in _EXPORTERS:
        flash("Invalid export format.", "danger")
        return redirect(url_for("vocab.list_entries"))

    query = VocabularyEntry.query.filter_by(user_id=current_user.id)
    if lecture:
        query = query.filter_by(lecture=lecture)
    entries = query.order_by(VocabularyEntry.lecture, VocabularyEntry.date_added).all()

    data = _EXPORTERS[fmt](entries)
    suffix = "xlsx" if fmt == "xlsx" else fmt
    filename = f"vocabulary.{suffix}"

    return send_file(
        io.BytesIO(data),
        mimetype=_MIME[fmt],
        as_attachment=True,
        download_name=filename,
    )


@bp.route("/import", methods=["GET", "POST"])
@login_required
def import_view():
    if request.method == "GET":
        return render_template("io/import.html")

    file = request.files.get("file")
    if not file or not file.filename:
        flash("Please choose a file.", "danger")
        return render_template("io/import.html")

    data = file.read()
    rows, global_errors = parse_file(file.filename, data)

    if global_errors:
        for err in global_errors:
            flash(err, "danger")
        return render_template("io/import.html")

    valid, duplicates, errors = validate_rows(rows, current_user.id)

    pending_path = save_pending(valid)
    session["import_pending"] = pending_path
    session["import_duplicates"] = [
        {k: v for k, v in r.items() if not k.startswith("_")} for r in duplicates
    ]

    return redirect(url_for("io.preview"))


@bp.route("/import/preview")
@login_required
def preview():
    pending_path = session.get("import_pending")
    if not pending_path:
        flash("No import in progress.", "warning")
        return redirect(url_for("io.import_view"))

    try:
        valid_rows = load_pending(pending_path)
    except Exception:
        flash("Import session expired. Please upload the file again.", "warning")
        session.pop("import_pending", None)
        session.pop("import_duplicates", None)
        return redirect(url_for("io.import_view"))

    duplicates = session.get("import_duplicates", [])
    sample = valid_rows[:5]

    return render_template(
        "io/preview.html",
        valid_count=len(valid_rows),
        dup_count=len(duplicates),
        duplicates=duplicates,
        sample=sample,
    )


@bp.route("/import/confirm", methods=["POST"])
@login_required
def confirm_import():
    pending_path = session.get("import_pending")
    if not pending_path:
        flash("No import in progress.", "warning")
        return redirect(url_for("io.import_view"))

    overwrite = request.form.get("overwrite") == "1"

    try:
        valid_rows = load_pending(pending_path)
    except Exception:
        flash("Import session expired. Please upload the file again.", "warning")
        session.pop("import_pending", None)
        session.pop("import_duplicates", None)
        return redirect(url_for("io.import_view"))

    # If overwrite, also include duplicates stored in session
    rows_to_import = valid_rows
    if overwrite:
        rows_to_import = valid_rows + session.get("import_duplicates", [])

    count = commit_import(rows_to_import, current_user.id, overwrite=overwrite)

    delete_pending(pending_path)
    session.pop("import_pending", None)
    session.pop("import_duplicates", None)

    flash(f"Successfully imported {count} word(s).", "success")
    return redirect(url_for("vocab.list_entries"))


@bp.route("/import/cancel")
@login_required
def cancel_import():
    pending_path = session.pop("import_pending", None)
    session.pop("import_duplicates", None)
    if pending_path:
        delete_pending(pending_path)
    flash("Import cancelled.", "info")
    return redirect(url_for("vocab.list_entries"))
