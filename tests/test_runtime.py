import unittest
from datetime import UTC, datetime, timedelta
from importlib.metadata import distribution, version

import django
from fsrs import Card, Rating, Scheduler, State


class InstalledRuntimeTests(unittest.TestCase):
    def test_django_and_package_entry_point_are_installed(self) -> None:
        self.assertEqual(django.get_version(), version("django"))
        entry_points = [entry for entry in distribution("oko").entry_points if entry.name == "oko"]
        self.assertEqual(len(entry_points), 1)
        self.assertTrue(callable(entry_points[0].load()))


class FsrsRuntimeTests(unittest.TestCase):
    answered_at = datetime(2026, 11, 8, 12, tzinfo=UTC)

    def test_default_learning_step_uses_explicit_answer_time(self) -> None:
        scheduler = Scheduler(enable_fuzzing=False)
        card, log = scheduler.review_card(
            Card(card_id=1, due=self.answered_at), Rating.Good, review_datetime=self.answered_at
        )

        self.assertEqual(card.state, State.Learning)
        self.assertEqual(card.due, self.answered_at + timedelta(minutes=10))
        self.assertEqual(log.review_datetime, self.answered_at)
        self.assertEqual(log.rating, Rating.Good)

    def test_long_term_review_uses_actual_late_answer_and_recall_decreases(self) -> None:
        scheduler = Scheduler(learning_steps=(), relearning_steps=(), enable_fuzzing=False)
        card, _ = scheduler.review_card(
            Card(card_id=2, due=self.answered_at), Rating.Good, review_datetime=self.answered_at
        )
        self.assertEqual(card.state, State.Review)
        self.assertGreater(card.due, self.answered_at)

        next_day = card.due + timedelta(days=1)
        next_week = next_day + timedelta(days=7)
        recall_next_day = scheduler.get_card_retrievability(card, next_day)
        recall_next_week = scheduler.get_card_retrievability(card, next_week)
        self.assertGreater(recall_next_day, recall_next_week)
        self.assertGreater(recall_next_week, 0)
        self.assertLess(recall_next_day, 1)

        reviewed, log = scheduler.review_card(card, Rating.Good, review_datetime=next_day)
        self.assertEqual(log.review_datetime, next_day)
        self.assertEqual(reviewed.last_review, next_day)
        self.assertGreater(reviewed.due, next_day)


if __name__ == "__main__":
    unittest.main()
