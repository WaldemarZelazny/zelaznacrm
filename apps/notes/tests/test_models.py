"""Testy modelu Note aplikacji notes."""

from __future__ import annotations

import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage
from apps.notes.models import Note


class NoteStrTest(TestCase):
    """Testy metody __str__ modelu Note."""

    def setUp(self) -> None:
        """Tworzy uzytkownika i notatke testowa."""
        self.author = User.objects.create_user(
            username="jan.kowalski",
            first_name="Jan",
            last_name="Kowalski",
        )

    def test_str_contains_short_content_and_author_full_name(self) -> None:
        """__str__ zawiera skrocona tresc i pelne imie autora."""
        note = Note.objects.create(
            content="Klient zainteresowany oferta.",
            author=self.author,
        )
        result = str(note)
        self.assertIn("Klient zainteresowany oferta.", result)
        self.assertIn("Jan Kowalski", result)
        self.assertTrue(result.startswith("Notatka:"))

    def test_str_uses_dash_when_no_author(self) -> None:
        """__str__ uzywa myslnika gdy brak autora."""
        note = Note.objects.create(content="Anonimowa notatka.")
        self.assertIn("—", str(note))

    def test_str_truncates_long_content(self) -> None:
        """__str__ zawiera '...' dla dlugich notatek."""
        long_content = "A" * 150
        note = Note.objects.create(content=long_content, author=self.author)
        self.assertIn("...", str(note))


class NoteShortContentTest(TestCase):
    """Testy wlasciwosci short_content."""

    def test_short_content_exact_limit(self) -> None:
        """Notatka o dlugosci == 100 nie dostaje wielokropka."""
        content = "X" * 100
        note = Note(content=content)
        self.assertEqual(note.short_content, content)
        self.assertNotIn("...", note.short_content)

    def test_short_content_over_limit_gets_ellipsis(self) -> None:
        """Notatka dluzsze niz 100 znakow otrzymuje '...' na koncu."""
        note = Note(content="B" * 101)
        self.assertTrue(note.short_content.endswith("..."))
        self.assertEqual(len(note.short_content), 103)  # 100 + "..."

    def test_short_content_under_limit_unchanged(self) -> None:
        """Krotka notatka zwracana jest bez zmian."""
        content = "Krotka notatka."
        note = Note(content=content)
        self.assertEqual(note.short_content, content)

    def test_short_content_empty_string(self) -> None:
        """Pusta tresc zwraca pusty string."""
        note = Note(content="")
        self.assertEqual(note.short_content, "")


class NoteRelatedObjectTest(TestCase):
    """Testy wlasciwosci related_object (priorytet: Deal > Lead > Company > Contact)."""

    def setUp(self) -> None:
        """Tworzy obiekty CRM potrzebne do testow."""
        self.company = Company.objects.create(name="Acme SA")
        self.contact = Contact.objects.create(
            first_name="Anna",
            last_name="Nowak",
            company=self.company,
        )
        self.stage = WorkflowStage.objects.get(name="Nowy")
        self.lead = Lead.objects.create(
            title="Lead testowy",
            company=self.company,
            stage=self.stage,
        )
        self.deal = Deal.objects.create(
            title="Umowa testowa",
            company=self.company,
            close_date=timezone.localdate() + datetime.timedelta(days=30),
        )

    def test_related_object_returns_deal_first(self) -> None:
        """related_object zwraca Deal gdy wszystkie pola ustawione."""
        note = Note(
            content="Test",
            deal=self.deal,
            lead=self.lead,
            company=self.company,
            contact=self.contact,
        )
        self.assertEqual(note.related_object, self.deal)

    def test_related_object_returns_lead_when_no_deal(self) -> None:
        """related_object zwraca Lead gdy brak Deal."""
        note = Note(
            content="Test",
            lead=self.lead,
            company=self.company,
            contact=self.contact,
        )
        self.assertEqual(note.related_object, self.lead)

    def test_related_object_returns_company_when_no_deal_lead(self) -> None:
        """related_object zwraca Company gdy brak Deal i Lead."""
        note = Note(
            content="Test",
            company=self.company,
            contact=self.contact,
        )
        self.assertEqual(note.related_object, self.company)

    def test_related_object_returns_contact_as_last_priority(self) -> None:
        """related_object zwraca Contact gdy tylko on jest ustawiony."""
        note = Note(content="Test", contact=self.contact)
        self.assertEqual(note.related_object, self.contact)

    def test_related_object_returns_none_when_no_relations(self) -> None:
        """related_object zwraca None gdy brak wszystkich powiazanych obiektow."""
        note = Note(content="Notatka bez powiazania.")
        self.assertIsNone(note.related_object)


class NoteDefaultsAndRelationsTest(TestCase):
    """Testy wartosci domyslnych i relacji modelu Note."""

    def setUp(self) -> None:
        """Tworzy dane bazowe."""
        self.user = User.objects.create_user(username="handlowiec")
        self.company = Company.objects.create(name="Beta Corp")

    def test_all_fk_optional(self) -> None:
        """Wszystkie FK sa opcjonalne – mozna stworzyc notatke bez powiazania."""
        note = Note.objects.create(content="Notatka minimalna.")
        self.assertIsNone(note.author)
        self.assertIsNone(note.company)
        self.assertIsNone(note.lead)
        self.assertIsNone(note.deal)
        self.assertIsNone(note.contact)

    def test_set_null_on_author_delete(self) -> None:
        """Usuniecie autora ustawia author=NULL (SET_NULL)."""
        note = Note.objects.create(content="Notatka.", author=self.user)
        self.user.delete()
        note.refresh_from_db()
        self.assertIsNone(note.author)

    def test_set_null_on_company_delete(self) -> None:
        """Usuniecie firmy ustawia company=NULL (SET_NULL), notatka zostaje."""
        note = Note.objects.create(content="Notatka firmowa.", company=self.company)
        note_id = note.pk
        self.company.delete()
        self.assertTrue(Note.objects.filter(pk=note_id).exists())
        note.refresh_from_db()
        self.assertIsNone(note.company)

    def test_ordering_newest_first(self) -> None:
        """Notatki sortowane od najnowszej."""
        Note.objects.create(content="Starsza notatka.")
        Note.objects.create(content="Nowsza notatka.")
        self.assertEqual(Note.objects.first().content, "Nowsza notatka.")

    def test_company_notes_reverse_accessor(self) -> None:
        """Odwrocona relacja z Company dostepna przez company_notes."""
        note = Note.objects.create(content="Notatka do firmy.", company=self.company)
        self.assertIn(note, self.company.company_notes.all())
