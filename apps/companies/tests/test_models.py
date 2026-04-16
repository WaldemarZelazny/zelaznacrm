"""Testy modelu Company aplikacji companies."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.companies.models import Company


class CompanyStrTest(TestCase):
    """Testy metody __str__ i właściwości modelu Company."""

    def setUp(self) -> None:
        """Tworzy przykładową firmę przed każdym testem."""
        self.owner = User.objects.create_user(username="handlowiec")
        self.company = Company.objects.create(
            name="Acme Sp. z o.o.",
            nip="1234567890",
            industry=Company.Industry.IT,
            address="ul. Testowa 1",
            city="Warszawa",
            postal_code="00-001",
            phone="22 100 200 300",
            email="biuro@acme.pl",
            owner=self.owner,
        )

    def test_str_returns_company_name(self) -> None:
        """__str__ zwraca nazwę firmy."""
        self.assertEqual(str(self.company), "Acme Sp. z o.o.")

    def test_full_address_all_parts(self) -> None:
        """full_address łączy adres, kod pocztowy i miasto."""
        self.assertEqual(self.company.full_address, "ul. Testowa 1, 00-001, Warszawa")

    def test_full_address_partial(self) -> None:
        """full_address pomija puste pola."""
        company = Company.objects.create(name="Bez adresu", city="Kraków")
        self.assertEqual(company.full_address, "Kraków")

    def test_full_address_empty(self) -> None:
        """full_address zwraca pusty string gdy brak wszystkich pól adresowych."""
        company = Company.objects.create(name="Anonimowa")
        self.assertEqual(company.full_address, "")


class CompanyDefaultsTest(TestCase):
    """Testy wartości domyślnych i opcjonalnych pól Company."""

    def test_default_industry_is_inne(self) -> None:
        """Domyślna branża to INNE."""
        company = Company.objects.create(name="Nowa Firma")
        self.assertEqual(company.industry, Company.Industry.INNE)

    def test_is_active_default_true(self) -> None:
        """Nowo dodana firma jest domyślnie aktywna."""
        company = Company.objects.create(name="Aktywna Firma")
        self.assertTrue(company.is_active)

    def test_optional_fields_blank_by_default(self) -> None:
        """Pola opcjonalne (nip, phone, email, website, notes) mogą być puste."""
        company = Company.objects.create(name="Minimalna Firma")
        self.assertEqual(company.nip, "")
        self.assertEqual(company.phone, "")
        self.assertEqual(company.email, "")
        self.assertEqual(company.website, "")
        self.assertEqual(company.notes, "")

    def test_owner_optional(self) -> None:
        """Pole owner (opiekun) jest opcjonalne – może być NULL."""
        company = Company.objects.create(name="Firma bez opiekuna")
        self.assertIsNone(company.owner)

    def test_ordering_by_name(self) -> None:
        """Firmy domyślnie sortowane są alfabetycznie po nazwie."""
        Company.objects.create(name="Zebra Corp")
        Company.objects.create(name="Alpha Ltd")
        Company.objects.create(name="Beta SA")
        names = list(Company.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))

    def test_industry_choices_count(self) -> None:
        """Liczba branż wynosi 10."""
        self.assertEqual(len(Company.Industry.choices), 10)

    def test_owner_set_null_on_user_delete(self) -> None:
        """Usunięcie User-a ustawia owner=NULL (SET_NULL), nie kasuje firmy."""
        user = User.objects.create_user(username="do_usuniecia")
        company = Company.objects.create(name="Osierocona Firma", owner=user)
        user.delete()
        company.refresh_from_db()
        self.assertIsNone(company.owner)
        self.assertTrue(Company.objects.filter(pk=company.pk).exists())
