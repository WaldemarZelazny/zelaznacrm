"""Testy modelu Contact aplikacji contacts."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.companies.models import Company
from apps.contacts.models import Contact


class ContactStrTest(TestCase):
    """Testy metody __str__ i właściwości modelu Contact."""

    def setUp(self) -> None:
        """Tworzy firmę i kontakt testowy przed każdym testem."""
        self.owner = User.objects.create_user(username="handlowiec")
        self.company = Company.objects.create(name="Acme Sp. z o.o.")
        self.contact = Contact.objects.create(
            first_name="Anna",
            last_name="Nowak",
            company=self.company,
            position="Dyrektor Zakupów",
            department=Contact.Department.ZAKUPY,
            email="anna.nowak@acme.pl",
            phone="22 100 200 300",
            mobile="600 700 800",
            owner=self.owner,
        )

    def test_str_includes_name_and_company(self) -> None:
        """__str__ zawiera imię, nazwisko i nazwę firmy."""
        self.assertEqual(str(self.contact), "Anna Nowak (Acme Sp. z o.o.)")

    def test_full_name_property(self) -> None:
        """full_name zwraca imię i nazwisko bez nazwy firmy."""
        self.assertEqual(self.contact.full_name, "Anna Nowak")

    def test_primary_phone_prefers_phone(self) -> None:
        """primary_phone zwraca telefon służbowy gdy istnieje."""
        self.assertEqual(self.contact.primary_phone, "22 100 200 300")

    def test_primary_phone_falls_back_to_mobile(self) -> None:
        """primary_phone zwraca komórkowy gdy brak telefonu służbowego."""
        self.contact.phone = ""
        self.assertEqual(self.contact.primary_phone, "600 700 800")

    def test_primary_phone_empty_when_no_phones(self) -> None:
        """primary_phone zwraca pusty string gdy brak obu numerów."""
        contact = Contact.objects.create(
            first_name="Bez",
            last_name="Telefonu",
            company=self.company,
        )
        self.assertEqual(contact.primary_phone, "")


class ContactDefaultsTest(TestCase):
    """Testy wartości domyślnych i relacji modelu Contact."""

    def setUp(self) -> None:
        """Tworzy firmę bazową dla testów."""
        self.company = Company.objects.create(name="Test Corp")

    def test_default_department_is_inne(self) -> None:
        """Domyślny dział to INNE."""
        contact = Contact.objects.create(
            first_name="Jan",
            last_name="Test",
            company=self.company,
        )
        self.assertEqual(contact.department, Contact.Department.INNE)

    def test_is_active_default_true(self) -> None:
        """Nowy kontakt jest domyślnie aktywny."""
        contact = Contact.objects.create(
            first_name="Jan",
            last_name="Test",
            company=self.company,
        )
        self.assertTrue(contact.is_active)

    def test_optional_fields_blank(self) -> None:
        """Pola opcjonalne mogą być puste bez błędu walidacji."""
        contact = Contact.objects.create(
            first_name="Minimalna",
            last_name="Osoba",
            company=self.company,
        )
        self.assertEqual(contact.position, "")
        self.assertEqual(contact.email, "")
        self.assertEqual(contact.phone, "")
        self.assertEqual(contact.mobile, "")
        self.assertIsNone(contact.owner)

    def test_cascade_delete_with_company(self) -> None:
        """Usunięcie firmy kasuje wszystkie powiązane kontakty."""
        contact = Contact.objects.create(
            first_name="Do",
            last_name="Usunięcia",
            company=self.company,
        )
        contact_id = contact.pk
        self.company.delete()
        self.assertFalse(Contact.objects.filter(pk=contact_id).exists())

    def test_owner_set_null_on_user_delete(self) -> None:
        """Usunięcie User-a ustawia owner=NULL, nie kasuje kontaktu."""
        user = User.objects.create_user(username="usuwany")
        contact = Contact.objects.create(
            first_name="Kontakt",
            last_name="Z Opiekunem",
            company=self.company,
            owner=user,
        )
        user.delete()
        contact.refresh_from_db()
        self.assertIsNone(contact.owner)

    def test_ordering_by_last_name_first_name(self) -> None:
        """Kontakty sortowane są po nazwisku, potem imieniu."""
        Contact.objects.create(
            first_name="Zbigniew", last_name="Zając", company=self.company
        )
        Contact.objects.create(
            first_name="Anna", last_name="Adamska", company=self.company
        )
        Contact.objects.create(
            first_name="Beata", last_name="Adamska", company=self.company
        )
        contacts = list(Contact.objects.values_list("first_name", "last_name"))
        self.assertEqual(contacts[0], ("Anna", "Adamska"))
        self.assertEqual(contacts[1], ("Beata", "Adamska"))
        self.assertEqual(contacts[2], ("Zbigniew", "Zając"))
