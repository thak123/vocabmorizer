import uuid
from datetime import date, datetime, timezone

from ..extensions import db


class VocabularyEntry(db.Model):
    __tablename__ = "vocabulary_entries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lecture = db.Column(db.String(200), nullable=False, index=True)
    date_added = db.Column(db.Date, nullable=False, default=date.today)
    word = db.Column(db.String(500), nullable=False)
    synonyms = db.Column(db.JSON, nullable=False, default=lambda: [])
    antonyms = db.Column(db.JSON, nullable=False, default=lambda: [])
    meaning = db.Column(db.Text, nullable=False)
    translation_en = db.Column(db.String(500), nullable=False)
    metadata_usage = db.Column(db.Text, nullable=True)
    target_language = db.Column(db.String(8), nullable=False, default="en")
    image_path = db.Column(db.String(500), nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = db.relationship(
        "User",
        backref=db.backref("vocabulary_entries", lazy="dynamic", passive_deletes=True),
    )
    review_stats = db.relationship(
        "ReviewStats",
        back_populates="entry",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<VocabularyEntry {self.word!r}>"


class ReviewStats(db.Model):
    __tablename__ = "review_stats"

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(
        db.String(36),
        db.ForeignKey("vocabulary_entries.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    times_reviewed = db.Column(db.Integer, nullable=False, default=0)
    correct_count = db.Column(db.Integer, nullable=False, default=0)
    consecutive_correct = db.Column(db.Integer, nullable=False, default=0)
    is_problematic = db.Column(db.Boolean, nullable=False, default=False)
    ease_factor = db.Column(db.Float, nullable=False, default=2.5)
    interval_days = db.Column(db.Integer, nullable=False, default=1)
    next_review_date = db.Column(db.Date, nullable=True)
    last_reviewed = db.Column(db.DateTime, nullable=True)

    entry = db.relationship("VocabularyEntry", back_populates="review_stats")
