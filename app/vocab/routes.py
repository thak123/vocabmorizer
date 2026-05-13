import uuid
from datetime import date

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models.vocabulary import ReviewStats, VocabularyEntry
from ..utils.helpers import delete_entry_image, save_entry_image
from . import bp
from .forms import VocabularyEntryForm


def _parse_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _entry_or_404(entry_id: str) -> VocabularyEntry:
    entry = db.session.get(VocabularyEntry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        from flask import abort
        abort(404)
    return entry


@bp.route("/")
@login_required
def list_entries():
    lecture_filter = request.args.get("lecture", "").strip()
    lang_filter = request.args.get("lang", "").strip()

    query = VocabularyEntry.query.filter_by(user_id=current_user.id).order_by(
        VocabularyEntry.date_added.desc(), VocabularyEntry.word
    )
    if lecture_filter:
        query = query.filter_by(lecture=lecture_filter)
    if lang_filter:
        query = query.filter_by(target_language=lang_filter)

    entries = query.all()

    lectures = [r[0] for r in (
        db.session.query(VocabularyEntry.lecture)
        .filter_by(user_id=current_user.id)
        .distinct()
        .order_by(VocabularyEntry.lecture)
        .all()
    )]
    langs = [r[0] for r in (
        db.session.query(VocabularyEntry.target_language)
        .filter_by(user_id=current_user.id)
        .distinct()
        .order_by(VocabularyEntry.target_language)
        .all()
    )]

    from .forms import LANGUAGE_CHOICES
    lang_names = dict(LANGUAGE_CHOICES)

    return render_template(
        "vocab/list.html",
        entries=entries,
        lectures=lectures,
        lecture_filter=lecture_filter,
        langs=langs,
        lang_filter=lang_filter,
        lang_names=lang_names,
    )


@bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = VocabularyEntryForm()
    if form.date_added.data is None:
        form.date_added.data = date.today()

    if form.validate_on_submit():
        entry_id = str(uuid.uuid4())
        image_path = save_entry_image(form.image.data, entry_id)

        entry = VocabularyEntry(
            id=entry_id,
            user_id=current_user.id,
            lecture=form.lecture.data.strip(),
            date_added=form.date_added.data,
            word=form.word.data.strip(),
            synonyms=_parse_csv(form.synonyms.data or ""),
            antonyms=_parse_csv(form.antonyms.data or ""),
            meaning=form.meaning.data.strip(),
            translation_en=form.translation_en.data.strip(),
            metadata_usage=form.metadata_usage.data.strip() if form.metadata_usage.data else None,
            target_language=form.target_language.data,
            image_path=image_path,
        )
        stats = ReviewStats(entry_id=entry_id)
        db.session.add(entry)
        db.session.add(stats)
        db.session.commit()
        flash(f"'{entry.word}' added successfully.", "success")
        return redirect(url_for("vocab.list_entries"))

    return render_template("vocab/add.html", form=form)


@bp.route("/<entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit(entry_id: str):
    entry = _entry_or_404(entry_id)
    form = VocabularyEntryForm(obj=entry)

    if request.method == "GET":
        form.synonyms.data = ", ".join(entry.synonyms or [])
        form.antonyms.data = ", ".join(entry.antonyms or [])

    if form.validate_on_submit():
        if form.image.data and form.image.data.filename:
            delete_entry_image(entry.image_path)
            entry.image_path = save_entry_image(form.image.data, entry.id)

        entry.lecture = form.lecture.data.strip()
        entry.date_added = form.date_added.data
        entry.word = form.word.data.strip()
        entry.synonyms = _parse_csv(form.synonyms.data or "")
        entry.antonyms = _parse_csv(form.antonyms.data or "")
        entry.meaning = form.meaning.data.strip()
        entry.translation_en = form.translation_en.data.strip()
        raw = form.metadata_usage.data
        entry.metadata_usage = raw.strip() if raw else None
        entry.target_language = form.target_language.data
        db.session.commit()
        flash(f"'{entry.word}' updated.", "success")
        return redirect(url_for("vocab.list_entries"))

    return render_template("vocab/edit.html", form=form, entry=entry)


@bp.route("/<entry_id>/delete", methods=["POST"])
@login_required
def delete(entry_id: str):
    entry = _entry_or_404(entry_id)
    delete_entry_image(entry.image_path)
    db.session.delete(entry)
    db.session.commit()
    flash(f"'{entry.word}' deleted.", "info")
    return redirect(url_for("vocab.list_entries"))


@bp.route("/<entry_id>/toggle-public", methods=["POST"])
@login_required
def toggle_public(entry_id: str):
    entry = _entry_or_404(entry_id)
    entry.is_public = not entry.is_public
    db.session.commit()
    return redirect(request.referrer or url_for("vocab.list_entries"))


@bp.route("/lecture/<path:lecture>/toggle-public", methods=["POST"])
@login_required
def toggle_lecture_public(lecture: str):
    make_public = request.form.get("make_public") == "1"
    VocabularyEntry.query.filter_by(
        user_id=current_user.id, lecture=lecture
    ).update({"is_public": make_public})
    db.session.commit()
    label = "public" if make_public else "private"
    flash(f"All entries in '{lecture}' set to {label}.", "success")
    return redirect(url_for("vocab.list_entries", lecture=lecture))


@bp.route("/community")
@login_required
def community():
    from ..models.user import User

    search = request.args.get("q", "").strip()
    lang_filter = request.args.get("lang", "").strip()
    user_filter = request.args.get("user_id", "").strip()

    query = VocabularyEntry.query.filter_by(is_public=True)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                VocabularyEntry.word.ilike(like),
                VocabularyEntry.meaning.ilike(like),
                VocabularyEntry.translation_en.ilike(like),
            )
        )
    if lang_filter:
        query = query.filter_by(target_language=lang_filter)
    if user_filter:
        query = query.filter_by(user_id=user_filter)

    entries = query.order_by(VocabularyEntry.user_id, VocabularyEntry.lecture, VocabularyEntry.word).all()

    # Group by user
    from collections import defaultdict
    by_user: dict = defaultdict(list)
    for e in entries:
        by_user[e.user_id].append(e)

    # Fetch user names
    user_ids = list(by_user.keys())
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()}

    # Available filter options
    langs = (
        db.session.query(VocabularyEntry.target_language)
        .filter_by(is_public=True)
        .distinct()
        .order_by(VocabularyEntry.target_language)
        .all()
    )
    langs = [r[0] for r in langs]

    return render_template(
        "vocab/community.html",
        by_user=by_user,
        users=users,
        total=len(entries),
        search=search,
        lang_filter=lang_filter,
        user_filter=user_filter,
        langs=langs,
    )
