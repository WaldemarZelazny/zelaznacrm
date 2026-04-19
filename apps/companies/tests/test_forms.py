"""Testy formularzy aplikacji companies."""

from __future__ import annotations

from django.test import TestCase

from apps.companies.forms import CompanyForm
from apps.companies.models import Company


class CompanyFormTest(TestCase):
    def _valid_data(self, **overrides) -> dict:
        data = {
            "name": "Testowa Sp. z o.o.",
            "nip": "1234567890",
            "industry": Company.Industry.IT,
            "phone": "600100200",
            "email": "biuro@testowa.pl",
            "website": "https://testowa.pl",
            "address": "ul. Testowa 1",
            "postal_code": "00-001",
            "city": "Warszawa",
            "notes": "",
            "is_active": True,
        }
        data.update(overrides)
        return data

    def test_valid_data_is_valid(self):
        form = CompanyForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name_invalid(self):
        form = CompanyForm(data=self._valid_data(name=""))
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_nip_optional(self):
        form = CompanyForm(data=self._valid_data(nip=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_phone_optional(self):
        form = CompanyForm(data=self._valid_data(phone=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_optional(self):
        form = CompanyForm(data=self._valid_data(email=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_website_optional(self):
        form = CompanyForm(data=self._valid_data(website=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_address_optional(self):
        form = CompanyForm(data=self._valid_data(address="", postal_code="", city=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email_format(self):
        form = CompanyForm(data=self._valid_data(email="niepoprawny-email"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_industry_choice(self):
        form = CompanyForm(data=self._valid_data(industry="NIEZNANA"))
        self.assertFalse(form.is_valid())
        self.assertIn("industry", form.errors)

    def test_is_active_defaults_unchecked(self):
        data = self._valid_data()
        del data["is_active"]
        form = CompanyForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["is_active"])

    def test_owner_not_in_form_fields(self):
        form = CompanyForm()
        self.assertNotIn("owner", form.fields)
