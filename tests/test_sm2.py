from datetime import date, timedelta

from app.practice.sm2 import MIN_EASE_FACTOR, calculate_next_review, update_problematic


class TestCalculateNextReview:
    def test_first_correct_review_gives_interval_1(self):
        r = calculate_next_review("correct", ease_factor=2.5, interval_days=1, times_reviewed=0)
        assert r.interval_days == 1

    def test_second_correct_review_gives_interval_6(self):
        r = calculate_next_review("correct", ease_factor=2.5, interval_days=1, times_reviewed=1)
        assert r.interval_days == 6

    def test_third_correct_multiplies_by_ef(self):
        r = calculate_next_review("correct", ease_factor=2.5, interval_days=6, times_reviewed=2)
        # EF increases after a correct answer, so new_interval = round(6 * new_ef) > 6
        assert r.interval_days == round(6 * r.ease_factor)

    def test_incorrect_resets_interval_to_1(self):
        r = calculate_next_review("incorrect", ease_factor=2.5, interval_days=20, times_reviewed=5)
        assert r.interval_days == 1

    def test_need_review_resets_interval(self):
        r = calculate_next_review(
            "need_review", ease_factor=2.5, interval_days=20, times_reviewed=5
        )
        assert r.interval_days == 1

    def test_ease_factor_increases_on_correct(self):
        r = calculate_next_review("correct", ease_factor=2.5, interval_days=1, times_reviewed=0)
        assert r.ease_factor > 2.5

    def test_ease_factor_decreases_on_incorrect(self):
        r = calculate_next_review("incorrect", ease_factor=2.5, interval_days=1, times_reviewed=0)
        assert r.ease_factor < 2.5

    def test_ease_factor_never_below_minimum(self):
        r = calculate_next_review(
            "incorrect", ease_factor=MIN_EASE_FACTOR, interval_days=1, times_reviewed=3
        )
        assert r.ease_factor >= MIN_EASE_FACTOR

    def test_next_review_date_is_in_future(self):
        r = calculate_next_review("correct", ease_factor=2.5, interval_days=1, times_reviewed=1)
        assert r.next_review_date >= date.today() + timedelta(days=1)

    def test_invalid_result_treated_as_incorrect(self):
        r = calculate_next_review("bogus", ease_factor=2.5, interval_days=10, times_reviewed=3)
        assert r.interval_days == 1


class TestUpdateProblematic:
    def test_not_flagged_below_3_reviews(self):
        _, is_prob = update_problematic(
            times_reviewed=1, correct_count=0, consecutive_correct=0, result="incorrect"
        )
        assert not is_prob

    def test_flagged_at_40_percent_incorrect_over_3_reviews(self):
        # 2 incorrect out of 5 = 40%
        _, is_prob = update_problematic(
            times_reviewed=4, correct_count=3, consecutive_correct=0, result="incorrect"
        )
        assert is_prob

    def test_not_flagged_below_40_percent(self):
        # 1 incorrect out of 5 = 20%
        _, is_prob = update_problematic(
            times_reviewed=4, correct_count=4, consecutive_correct=0, result="incorrect"
        )
        assert not is_prob

    def test_flag_clears_after_3_consecutive_correct(self):
        _, is_prob = update_problematic(
            times_reviewed=10, correct_count=4, consecutive_correct=2, result="correct"
        )
        assert not is_prob

    def test_consecutive_correct_resets_on_incorrect(self):
        new_consec, _ = update_problematic(
            times_reviewed=5, correct_count=5, consecutive_correct=2, result="incorrect"
        )
        assert new_consec == 0

    def test_consecutive_correct_increments_on_correct(self):
        new_consec, _ = update_problematic(
            times_reviewed=5, correct_count=4, consecutive_correct=1, result="correct"
        )
        assert new_consec == 2
