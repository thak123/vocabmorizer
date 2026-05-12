"""
SM-2 spaced repetition algorithm.

Quality scale (mapped from user response):
  correct      → 5
  need_review  → 3
  incorrect    → 1

Reference: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

QUALITY_MAP = {
    "correct": 5,
    "need_review": 2,  # triggers interval reset; EF decays
    "incorrect": 1,
}

MIN_EASE_FACTOR = 1.3


@dataclass
class SM2Result:
    ease_factor: float
    interval_days: int
    next_review_date: date


def calculate_next_review(
    result: str,
    ease_factor: float,
    interval_days: int,
    times_reviewed: int,
) -> SM2Result:
    """Return updated SM-2 state after a review.

    result: one of 'correct', 'need_review', 'incorrect'
    ease_factor: current EF (default 2.5 for new cards)
    interval_days: current interval (1 for new cards)
    times_reviewed: number of reviews completed so far (before this one)
    """
    quality = QUALITY_MAP.get(result, 1)

    # Update ease factor
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(MIN_EASE_FACTOR, round(new_ef, 4))

    if quality < 3:
        # Failed — restart interval but keep accumulated EF
        new_interval = 1
    elif times_reviewed == 0:
        new_interval = 1
    elif times_reviewed == 1:
        new_interval = 6
    else:
        new_interval = max(1, round(interval_days * new_ef))

    next_date = date.today() + timedelta(days=new_interval)
    return SM2Result(ease_factor=new_ef, interval_days=new_interval, next_review_date=next_date)


def update_problematic(
    times_reviewed: int,
    correct_count: int,
    consecutive_correct: int,
    result: str,
) -> tuple[int, bool]:
    """Return (new_consecutive_correct, is_problematic).

    A word is flagged problematic when incorrect_rate >= 40% over >= 3 reviews.
    The flag clears after 3 consecutive correct answers.
    """
    if result == "correct":
        new_consecutive = consecutive_correct + 1
    else:
        new_consecutive = 0

    # Compute after this review
    total = times_reviewed + 1
    correct = correct_count + (1 if result == "correct" else 0)

    if new_consecutive >= 3:
        return new_consecutive, False

    incorrect_rate = (total - correct) / total if total > 0 else 0
    is_problematic = total >= 3 and incorrect_rate >= 0.4

    return new_consecutive, is_problematic
