"""Testy modeli WorkflowStage i Lead aplikacji leads."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.models import Lead, WorkflowStage


class WorkflowStageTest(TestCase):
    """Testy modelu WorkflowStage."""

    def test_str_includes_order_and_name(self) -> None:
        """__str__ zwraca numer kolejności i nazwę etapu."""
        stage = WorkflowStage.objects.create(name="Testowy", order=3)
        self.assertEqual(str(stage), "3. Testowy")

    def test_default_stages_created_by_migration(self) -> None:
        """Migracja danych tworzy 6 domyślnych etapów."""
        self.assertEqual(WorkflowStage.objects.count(), 6)

    def test_stages_ordered_by_order_field(self) -> None:
        """Etapy domyślnie sortowane wg pola order."""
        names = list(WorkflowStage.objects.values_list("name", flat=True))
        self.assertEqual(names[0], "Nowy")
        self.assertEqual(names[-1], "Przegrana")

    def test_default_color_hex(self) -> None:
        """Domyślny kolor etapu to szary (#6c757d)."""
        stage = WorkflowStage.objects.create(name="Bez koloru", order=99)
        self.assertEqual(stage.color, "#6c757d")


class LeadStrAndPropertiesTest(TestCase):
    """Testy __str__ i właściwości modelu Lead."""

    def setUp(self) -> None:
        """Tworzy dane testowe: user, firma, kontakt, etap, lead."""
        self.user = User.objects.create_user(username="handlowiec")
        self.company = Company.objects.create(name="Acme Sp. z o.o.")
        self.contact = Contact.objects.create(
            first_name="Jan",
            last_name="Kowalski",
            company=self.company,
        )
        self.stage = WorkflowStage.objects.get(name="Nowy")
        self.lead = Lead.objects.create(
            title="Dostawa sprzętu IT",
            company=self.company,
            contact=self.contact,
            owner=self.user,
            status=Lead.Status.NOWY,
            source=Lead.Source.POLECENIE,
            value=Decimal("15000.00"),
            stage=self.stage,
        )

    def test_str_contains_title_and_company(self) -> None:
        """__str__ zawiera tytuł leada i nazwę firmy."""
        self.assertEqual(str(self.lead), "Dostawa sprzętu IT – Acme Sp. z o.o.")

    def test_is_closed_false_for_open_lead(self) -> None:
        """is_closed == False dla otwartego leada (status NOWY / W_TOKU)."""
        self.assertFalse(self.lead.is_closed)

    def test_is_closed_true_for_wygrana(self) -> None:
        """is_closed == True gdy status WYGRANA."""
        self.lead.status = Lead.Status.WYGRANA
        self.assertTrue(self.lead.is_closed)

    def test_is_closed_true_for_przegrana(self) -> None:
        """is_closed == True gdy status PRZEGRANA."""
        self.lead.status = Lead.Status.PRZEGRANA
        self.assertTrue(self.lead.is_closed)

    def test_is_closed_true_for_anulowany(self) -> None:
        """is_closed == True gdy status ANULOWANY."""
        self.lead.status = Lead.Status.ANULOWANY
        self.assertTrue(self.lead.is_closed)

    def test_value_display_format(self) -> None:
        """value_display formatuje wartość z jednostką PLN."""
        self.assertIn("PLN", self.lead.value_display)
        self.assertIn("15", self.lead.value_display)


class LeadCloseMethodTest(TestCase):
    """Testy metody close() modelu Lead."""

    def setUp(self) -> None:
        """Tworzy otwarty lead do zamykania."""
        self.user = User.objects.create_user(username="sprzedawca")
        self.company = Company.objects.create(name="Beta Corp")
        self.stage = WorkflowStage.objects.get(name="Nowy")
        self.lead = Lead.objects.create(
            title="Lead do zamknięcia",
            company=self.company,
            owner=self.user,
            stage=self.stage,
        )

    def test_close_sets_status_wygrana(self) -> None:
        """close(WYGRANA) ustawia status i zapisuje do bazy."""
        self.lead.close(Lead.Status.WYGRANA)
        self.lead.refresh_from_db()
        self.assertEqual(self.lead.status, Lead.Status.WYGRANA)

    def test_close_sets_closed_at_to_now(self) -> None:
        """close() ustawia closed_at na aktualny czas."""
        before = timezone.now()
        self.lead.close(Lead.Status.PRZEGRANA)
        self.lead.refresh_from_db()
        self.assertIsNotNone(self.lead.closed_at)
        self.assertGreaterEqual(self.lead.closed_at, before)

    def test_close_with_invalid_status_raises_value_error(self) -> None:
        """close() z nieprawidłowym statusem rzuca ValueError."""
        with self.assertRaises(ValueError):
            self.lead.close(Lead.Status.NOWY)

    def test_close_with_w_toku_raises_value_error(self) -> None:
        """close() ze statusem W_TOKU rzuca ValueError."""
        with self.assertRaises(ValueError):
            self.lead.close(Lead.Status.W_TOKU)


class LeadDefaultsAndRelationsTest(TestCase):
    """Testy wartości domyślnych i relacji modelu Lead."""

    def setUp(self) -> None:
        """Tworzy minimalne dane testowe."""
        self.company = Company.objects.create(name="Gamma SA")
        self.stage = WorkflowStage.objects.get(name="Nowy")

    def test_default_status_is_nowy(self) -> None:
        """Domyślny status nowego leada to NOWY."""
        lead = Lead.objects.create(title="Test", company=self.company, stage=self.stage)
        self.assertEqual(lead.status, Lead.Status.NOWY)

    def test_default_value_is_zero(self) -> None:
        """Domyślna wartość leada to 0."""
        lead = Lead.objects.create(title="Test", company=self.company, stage=self.stage)
        self.assertEqual(lead.value, Decimal("0"))

    def test_contact_optional(self) -> None:
        """Pole contact jest opcjonalne (null=True)."""
        lead = Lead.objects.create(
            title="Bez kontaktu", company=self.company, stage=self.stage
        )
        self.assertIsNone(lead.contact)

    def test_cascade_delete_with_company(self) -> None:
        """Usunięcie firmy kasuje powiązane leady (CASCADE)."""
        lead = Lead.objects.create(
            title="Do usunięcia", company=self.company, stage=self.stage
        )
        lead_id = lead.pk
        self.company.delete()
        self.assertFalse(Lead.objects.filter(pk=lead_id).exists())

    def test_ordering_newest_first(self) -> None:
        """Leady domyślnie sortowane od najnowszego."""
        Lead.objects.create(title="Starszy", company=self.company, stage=self.stage)
        Lead.objects.create(title="Nowszy", company=self.company, stage=self.stage)
        first_title = Lead.objects.first().title
        self.assertEqual(first_title, "Nowszy")
