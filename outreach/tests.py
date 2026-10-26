from django.test import TestCase

# Create your tests here.
from datetime import date, timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase

from outreach.services.scheduler import (
    partner_date_has_spacing_conflict,
    choose_best_candidate_for_partner_slot,
)


class PartnerSpacingTests(SimpleTestCase):

    def test_rejects_dates_less_than_21_days_apart(self):
        existing_dates = {date(2027, 6, 5)}

        self.assertTrue(
            partner_date_has_spacing_conflict(
                event_date=date(2027, 6, 19),
                partner_dates=existing_dates,
                minimum_gap_days=21,
            )
        )

    def test_allows_dates_exactly_21_days_apart(self):
        existing_dates = {date(2027, 6, 5)}

        self.assertFalse(
            partner_date_has_spacing_conflict(
                event_date=date(2027, 6, 26),
                partner_dates=existing_dates,
                minimum_gap_days=21,
            )
        )

    def test_checks_dates_before_and_after_existing_events(self):
        existing_dates = {date(2027, 6, 26)}

        self.assertTrue(
            partner_date_has_spacing_conflict(
                event_date=date(2027, 6, 12),
                partner_dates=existing_dates,
                minimum_gap_days=21,
            )
        )


class SchedulingStrategyTests(SimpleTestCase):

    def setUp(self):
        self.candidates = [
            {
                "event_date": date(2027, 6, 5),
                "score": 1300,
            },
            {
                "event_date": date(2027, 6, 26),
                "score": 1390,
            },
            {
                "event_date": date(2027, 7, 3),
                "score": 1350,
            },
        ]

    def choose(self, strategy, used_months=None):
        partner = SimpleNamespace(
            scheduling_strategy=strategy,
            events_per_year=6,
        )

        return choose_best_candidate_for_partner_slot(
            partner=partner,
            partner_candidates=self.candidates,
            target_month=6,
            used_dates=set(),
            existing_suggested_dates=set(),
            used_months=used_months or set(),
            partner_dates=set(),
        )

    def test_strict_strategy_prevents_second_event_in_month(self):
        chosen = self.choose(
            strategy="STRICT",
            used_months={6},
        )

        self.assertEqual(
            chosen["event_date"],
            date(2027, 7, 3),
        )

    def test_flexible_strategy_can_reuse_month(self):
        chosen = self.choose(
            strategy="FLEXIBLE",
            used_months={6},
        )

        self.assertEqual(
            chosen["event_date"],
            date(2027, 6, 26),
        )

    def test_strict_strategy_prefers_target_month(self):
        chosen = self.choose(strategy="STRICT")

        self.assertEqual(
            chosen["event_date"],
            date(2027, 6, 26),
        )

    def test_existing_calendar_dates_are_excluded(self):
        partner = SimpleNamespace(
            scheduling_strategy="FLEXIBLE",
            events_per_year=6,
        )

        chosen = choose_best_candidate_for_partner_slot(
            partner=partner,
            partner_candidates=self.candidates,
            target_month=6,
            used_dates={date(2027, 6, 26)},
            existing_suggested_dates=set(),
            used_months=set(),
            partner_dates=set(),
        )

        self.assertNotEqual(
            chosen["event_date"],
            date(2027, 6, 26),
        )