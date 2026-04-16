"""Testy modelu Deal aplikacji deals."""

from __future__ import annotations

import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage


class DealStrAndPropertiesTest(TestCase):
    """Testy __str__ i właściwości modelu Deal."""

    def setUp(self) -> None:
        """Tworzy dane testowe: user, firma, umowa."""
        self.user = User.objects.create_user(username="handlowiec")
        self.company = Company.objects.create(name="Gamma SA")
        self.tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        self.yesterday = timezone.localdate() - datetime.timedelta(days=1)
        self.deal = Deal.objects.create(
            title="Wdrożenie systemu CRM",
            company=self.company,
            owner=self.user,
            value=Decimal("50000.00"),
            close_date=self.tomorrow,
        )

    def test_str_contains_title_and_company(self) -> None:
        """__str__ zawiera tytuł umowy i nazwę firmy."""
        self.assertEqual(str(self.deal), "Wdrożenie systemu CRM – Gamma SA")

    def test_is_active_true_by_default(self) -> None:
        """Nowa umowa jest domyślnie aktywna."""
        self.assertTrue(self.deal.is_active)

    def test_is_active_false_when_completed(self) -> None:
        """is_active == False po zrealizowaniu umowy."""
        self.deal.status = Deal.Status.ZREALIZOWANA
        self.assertFalse(self.deal.is_active)

    def test_is_overdue_false_for_future_close_date(self) -> None:
        """is_overdue == False gdy termin jest w przyszłości."""
        self.assertFalse(self.deal.is_overdue)

    def test_is_overdue_true_for_past_close_date_and_active(self) -> None:
        """is_overdue == True gdy termin minął i umowa aktywna."""
        self.deal.close_date = self.yesterday
        self.assertTrue(self.deal.is_overdue)

    def test_is_overdue_false_for_completed_deal(self) -> None:
        """is_overdue == False dla zrealizowanej umowy, nawet po terminie."""
        self.deal.close_date = self.yesterday
        self.deal.status = Deal.Status.ZREALIZOWANA
        self.assertFalse(self.deal.is_overdue)

    def test_value_display_contains_pln(self) -> None:
        """value_display zawiera jednostke PLN."""
        self.assertIn("PLN", self.deal.value_display)
        self.assertIn("50", self.deal.value_display)


class DealCompleteMethodTest(TestCase):
    """Testy metody complete() modelu Deal."""

    def setUp(self) -> None:
        """Tworzy aktywna umowe do testow complete()."""
        self.company = Company.objects.create(name="Alpha Sp. z o.o.")
        self.deal = Deal.objects.create(
            title="Umowa testowa",
            company=self.company,
            close_date=timezone.localdate() + datetime.timedelta(days=30),
        )

    def test_complete_sets_status_zrealizowana(self) -> None:
        """complete() ustawia status ZREALIZOWANA i zapisuje do bazy."""
        self.deal.complete()
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.status, Deal.Status.ZREALIZOWANA)

    def test_complete_sets_signed_at_to_today(self) -> None:
        """complete() ustawia signed_at = dzisiaj gdy pole bylo puste."""
        self.deal.complete()
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.signed_at, timezone.localdate())

    def test_complete_preserves_existing_signed_at(self) -> None:
        """complete() nie nadpisuje signed_at gdy juz ustawione."""
        past_date = timezone.localdate() - datetime.timedelta(days=10)
        self.deal.signed_at = past_date
        self.deal.save()
        self.deal.complete()
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.signed_at, past_date)

    def test_complete_raises_for_cancelled_deal(self) -> None:
        """complete() rzuca ValueError dla anulowanej umowy."""
        self.deal.status = Deal.Status.ANULOWANA
        self.deal.save()
        with self.assertRaises(ValueError):
            self.deal.complete()


class DealCancelMethodTest(TestCase):
    """Testy metody cancel() modelu Deal."""

    def setUp(self) -> None:
        """Tworzy aktywna umowe do testow cancel()."""
        self.company = Company.objects.create(name="Beta Corp")
        self.deal = Deal.objects.create(
            title="Umowa do anulowania",
            company=self.company,
            close_date=timezone.localdate() + datetime.timedelta(days=7),
        )

    def test_cancel_sets_status_anulowana(self) -> None:
        """cancel() ustawia status ANULOWANA i zapisuje do bazy."""
        self.deal.cancel()
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.status, Deal.Status.ANULOWANA)

    def test_cancel_idempotent_for_already_cancelled(self) -> None:
        """cancel() na juz anulowanej umowie jest bezpieczne."""
        self.deal.status = Deal.Status.ANULOWANA
        self.deal.save()
        self.deal.cancel()
        self.assertEqual(self.deal.status, Deal.Status.ANULOWANA)

    def test_cancel_raises_for_completed_deal(self) -> None:
        """cancel() rzuca ValueError dla zrealizowanej umowy."""
        self.deal.status = Deal.Status.ZREALIZOWANA
        self.deal.save()
        with self.assertRaises(ValueError):
            self.deal.cancel()


class DealDefaultsAndRelationsTest(TestCase):
    """Testy wartosci domyslnych i relacji modelu Deal."""

    def setUp(self) -> None:
        """Tworzy dane bazowe."""
        self.company = Company.objects.create(name="Delta Inc")
        self.close_date = timezone.localdate() + datetime.timedelta(days=14)

    def test_default_status_is_aktywna(self) -> None:
        """Domyslny status nowej umowy to AKTYWNA."""
        deal = Deal.objects.create(
            title="Test", company=self.company, close_date=self.close_date
        )
        self.assertEqual(deal.status, Deal.Status.AKTYWNA)

    def test_default_value_is_zero(self) -> None:
        """Domyslna wartosc umowy to 0."""
        deal = Deal.objects.create(
            title="Test", company=self.company, close_date=self.close_date
        )
        self.assertEqual(deal.value, Decimal("0"))

    def test_lead_optional(self) -> None:
        """Pole lead jest opcjonalne (null=True, blank=True)."""
        deal = Deal.objects.create(
            title="Bez leada", company=self.company, close_date=self.close_date
        )
        self.assertIsNone(deal.lead)

    def test_lead_set_null_on_lead_delete(self) -> None:
        """Usuniecie Lead-a ustawia deal.lead=NULL, nie kasuje umowy."""
        stage = WorkflowStage.objects.get(name="Nowy")
        lead = Lead.objects.create(
            title="Lead do usuniecia", company=self.company, stage=stage
        )
        deal = Deal.objects.create(
            title="Umowa z leadem",
            company=self.company,
            lead=lead,
            close_date=self.close_date,
        )
        lead.delete()
        deal.refresh_from_db()
        self.assertIsNone(deal.lead)

    def test_cascade_delete_with_company(self) -> None:
        """Usuniecie firmy kasuje powiazane umowy (CASCADE)."""
        deal = Deal.objects.create(
            title="Do usuniecia", company=self.company, close_date=self.close_date
        )
        deal_id = deal.pk
        self.company.delete()
        self.assertFalse(Deal.objects.filter(pk=deal_id).exists())

    def test_ordering_newest_first(self) -> None:
        """Umowy domyslnie sortowane od najnowszej."""
        Deal.objects.create(
            title="Starsza", company=self.company, close_date=self.close_date
        )
        Deal.objects.create(
            title="Nowsza", company=self.company, close_date=self.close_date
        )
        self.assertEqual(Deal.objects.first().title, "Nowsza")
