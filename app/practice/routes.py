import random
from datetime import date, datetime, timezone

from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models.vocabulary import ReviewStats, VocabularyEntry
from . import bp
from .sm2 import calculate_next_review, update_problematic

PRACTICE_SESSION_KEY = "practice"


def _build_queue(
    user_id: str,
    lecture: str | None,
    mode: str,
    date_from: str | None,
    date_to: str | None,
) -> list[str]:
    """Return an ordered list of entry IDs matching the filter criteria."""
    query = VocabularyEntry.query.filter_by(user_id=user_id)

    if lecture:
        query = query.filter_by(lecture=lecture)

    if date_from:
        try:
            query = query.filter(VocabularyEntry.date_added >= date.fromisoformat(date_from))
        except ValueError:
            pass

    if date_to:
        try:
            query = query.filter(VocabularyEntry.date_added <= date.fromisoformat(date_to))
        except ValueError:
            pass

    if mode == "problematic":
        query = query.join(ReviewStats).filter(ReviewStats.is_problematic.is_(True))
    elif mode == "due":
        today = date.today()
        query = query.join(ReviewStats).filter(
            (ReviewStats.next_review_date <= today) | ReviewStats.next_review_date.is_(None)
        )

    entries = query.all()

    if mode == "random":
        random.shuffle(entries)

    return [e.id for e in entries]


@bp.route("/", methods=["GET"])
@login_required
def setup():
    lectures = (
        db.session.query(VocabularyEntry.lecture)
        .filter_by(user_id=current_user.id)
        .distinct()
        .order_by(VocabularyEntry.lecture)
        .all()
    )
    lectures = [r[0] for r in lectures]
    total = VocabularyEntry.query.filter_by(user_id=current_user.id).count()
    problematic = (
        VocabularyEntry.query.filter_by(user_id=current_user.id)
        .join(ReviewStats)
        .filter(ReviewStats.is_problematic.is_(True))
        .count()
    )
    due = (
        VocabularyEntry.query.filter_by(user_id=current_user.id)
        .join(ReviewStats)
        .filter(
            (ReviewStats.next_review_date <= date.today()) | ReviewStats.next_review_date.is_(None)
        )
        .count()
    )
    return render_template(
        "practice/setup.html",
        lectures=lectures,
        total=total,
        problematic=problematic,
        due=due,
    )


@bp.route("/start", methods=["POST"])
@login_required
def start():
    lecture = request.form.get("lecture", "").strip() or None
    mode = request.form.get("mode", "all")
    date_from = request.form.get("date_from", "").strip() or None
    date_to = request.form.get("date_to", "").strip() or None

    queue = _build_queue(current_user.id, lecture, mode, date_from, date_to)
    if not queue:
        flash("No vocabulary entries match those filters.", "warning")
        return redirect(url_for("practice.setup"))

    session[PRACTICE_SESSION_KEY] = {"queue": queue, "index": 0, "results": {}}
    return redirect(url_for("practice.card"))


@bp.route("/card")
@login_required
def card():
    state = session.get(PRACTICE_SESSION_KEY)
    if not state:
        return redirect(url_for("practice.setup"))

    queue = state["queue"]
    index = state["index"]

    if index >= len(queue):
        return redirect(url_for("practice.done"))

    entry = db.session.get(VocabularyEntry, queue[index])
    if entry is None or entry.user_id != current_user.id:
        abort(404)

    return render_template(
        "practice/card.html",
        entry=entry,
        index=index,
        total=len(queue),
    )


@bp.route("/record", methods=["POST"])
@login_required
def record():
    state = session.get(PRACTICE_SESSION_KEY)
    if not state:
        return jsonify({"error": "No active session"}), 400

    data = request.get_json(silent=True) or {}
    entry_id = data.get("entry_id")
    result = data.get("result")

    if result not in ("correct", "need_review", "incorrect"):
        return jsonify({"error": "Invalid result"}), 400

    entry = db.session.get(VocabularyEntry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        return jsonify({"error": "Not found"}), 404

    stats = entry.review_stats
    if stats is None:
        stats = ReviewStats(entry_id=entry_id)
        db.session.add(stats)

    sm2 = calculate_next_review(
        result=result,
        ease_factor=stats.ease_factor,
        interval_days=stats.interval_days,
        times_reviewed=stats.times_reviewed,
    )

    new_consecutive, is_problematic = update_problematic(
        times_reviewed=stats.times_reviewed,
        correct_count=stats.correct_count,
        consecutive_correct=stats.consecutive_correct,
        result=result,
    )

    stats.times_reviewed += 1
    if result == "correct":
        stats.correct_count += 1
    stats.consecutive_correct = new_consecutive
    stats.is_problematic = is_problematic
    stats.ease_factor = sm2.ease_factor
    stats.interval_days = sm2.interval_days
    stats.next_review_date = sm2.next_review_date
    stats.last_reviewed = datetime.now(timezone.utc)

    # Track result in session for done-page summary
    state["results"][entry_id] = result
    state["index"] += 1
    session[PRACTICE_SESSION_KEY] = state
    session.modified = True

    db.session.commit()

    if state["index"] >= len(state["queue"]):
        return jsonify({"next": url_for("practice.done")})
    return jsonify({"next": url_for("practice.card")})


@bp.route("/done")
@login_required
def done():
    state = session.pop(PRACTICE_SESSION_KEY, {})
    results = state.get("results", {})
    correct = sum(1 for r in results.values() if r == "correct")
    need_review = sum(1 for r in results.values() if r == "need_review")
    incorrect = sum(1 for r in results.values() if r == "incorrect")
    total = len(results)
    return render_template(
        "practice/done.html",
        total=total,
        correct=correct,
        need_review=need_review,
        incorrect=incorrect,
    )
