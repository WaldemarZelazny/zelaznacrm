"""Testy formularzy aplikacji contacts."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.contacts.forms import ContactForm


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    user = User.objects.create_user(username=username, password="pass")
    user.profile.role = role
    user.profile.save()
    return user


def _make_company(name: str, owner: User) -> Company:
    return Company.objects.create(name=name, owner=owner)


class ContactFormTest(TestCase):
    def setUp(self):
        self.admin = _make_user("admin", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec")
        self.own_company = _make_company("Własna Sp. z o.o.", self.handlowiec)
        self.other_company = _make_company("Obca Sp. z o.o.", self.admin)

    def _valid_data(self, **overrides) -> dict:
        data = {
            "first_name": "Anna",
            "last_name": "Kowalska",
            "company": self.own_company.pk,
            "position": "",
            "department": "SPRZEDAZ",
            "email": "anna@example.com",
            "phone": "",
            "mobile": "",
            "notes": "",
            "is_active": True,
        }
        data.update(overrides)
        return data

    def test_valid_data_is_valid(self):
        form = ContactForm(data=self._valid_data(), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_first_name_invalid(self):
        form = ContactForm(data=self._valid_data(first_name=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_missing_last_name_invalid(self):
        form = ContactForm(data=self._valid_data(last_name=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)

    def test_company_required(self):
        form = ContactForm(data=self._valid_data(company=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    def test_optional_fields_empty_valid(self):
        form = ContactForm(
            data=self._valid_data(position="", email="", phone="", mobile=""),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email_format(self):
        form = ContactForm(
            data=self._valid_data(email="nie-email"), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    # --- Dynamiczny queryset per rola ---

    def test_handlowiec_sees_only_own_companies(self):
        form = ContactForm(user=self.handlowiec)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertNotIn(self.other_company, qs)

    def test_admin_sees_all_companies(self):
        form = ContactForm(user=self.admin)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertIn(self.other_company, qs)

    def test_handlowiec_cannot_assign_foreign_company(self):
        form = ContactForm(
            data=self._valid_data(company=self.other_company.pk),
            user=self.handlowiec,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    def test_admin_can_assign_any_company(self):
        form = ContactForm(
            data=self._valid_data(company=self.other_company.pk),
            user=self.admin,
        )
        self.assertTrue(form.is_valid(), form.errors)
