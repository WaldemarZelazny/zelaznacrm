"""Testy formularzy aplikacji leads."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.leads.forms import LeadForm
from apps.leads.models import Lead, WorkflowStage


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    user = User.objects.create_user(username=username, password="pass")
    user.profile.role = role
    user.profile.save()
    return user


def _make_company(name: str, owner: User) -> Company:
    return Company.objects.create(name=name, owner=owner)


def _make_contact(first: str, last: str, company: Company, owner: User) -> Contact:
    return Contact.objects.create(
        first_name=first, last_name=last, company=company, owner=owner
    )


def _make_stage(name: str, order: int = 1, is_active: bool = True) -> WorkflowStage:
    return WorkflowStage.objects.create(name=name, order=order, is_active=is_active)


class LeadFormTest(TestCase):
    def setUp(self):
        self.admin = _make_user("admin", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec")
        self.own_company = _make_company("Własna Sp. z o.o.", self.handlowiec)
        self.other_company = _make_company("Obca Sp. z o.o.", self.admin)
        self.own_contact = _make_contact(
            "Jan", "Kowalski", self.own_company, self.handlowiec
        )
        self.other_contact = _make_contact(
            "Anna", "Nowak", self.other_company, self.admin
        )
        self.stage = _make_stage("Kwalifikacja", order=1)
        self.inactive_stage = _make_stage("Archiwum", order=99, is_active=False)

    def _valid_data(self, **overrides) -> dict:
        data = {
            "title": "Nowy lead testowy",
            "company": self.own_company.pk,
            "contact": "",
            "source": Lead.Source.INNE,
            "value": "5000.00",
            "stage": self.stage.pk,
            "description": "",
        }
        data.update(overrides)
        return data

    # --- Poprawne dane ---

    def test_valid_data_is_valid(self):
        form = LeadForm(data=self._valid_data(), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_contact_is_valid(self):
        form = LeadForm(
            data=self._valid_data(contact=self.own_contact.pk), user=self.handlowiec
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Brakujące wymagane pola ---

    def test_missing_title_invalid(self):
        form = LeadForm(data=self._valid_data(title=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_missing_company_invalid(self):
        form = LeadForm(data=self._valid_data(company=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    def test_missing_stage_invalid(self):
        form = LeadForm(data=self._valid_data(stage=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("stage", form.errors)

    def test_contact_optional(self):
        form = LeadForm(data=self._valid_data(contact=""), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_zero_value_valid(self):
        form = LeadForm(data=self._valid_data(value="0"), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    # --- Dynamiczny queryset: company ---

    def test_handlowiec_sees_only_own_companies(self):
        form = LeadForm(user=self.handlowiec)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertNotIn(self.other_company, qs)

    def test_admin_sees_all_companies(self):
        form = LeadForm(user=self.admin)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertIn(self.other_company, qs)

    def test_handlowiec_cannot_assign_foreign_company(self):
        form = LeadForm(
            data=self._valid_data(company=self.other_company.pk), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    def test_admin_can_assign_any_company(self):
        form = LeadForm(
            data=self._valid_data(company=self.other_company.pk), user=self.admin
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Dynamiczny queryset: contact ---

    def test_handlowiec_sees_only_own_contacts(self):
        form = LeadForm(user=self.handlowiec)
        qs = form.fields["contact"].queryset
        self.assertIn(self.own_contact, qs)
        self.assertNotIn(self.other_contact, qs)

    def test_admin_sees_all_contacts(self):
        form = LeadForm(user=self.admin)
        qs = form.fields["contact"].queryset
        self.assertIn(self.own_contact, qs)
        self.assertIn(self.other_contact, qs)

    # --- Stage: tylko aktywne ---

    def test_stage_queryset_only_active(self):
        form = LeadForm(user=self.handlowiec)
        qs = form.fields["stage"].queryset
        self.assertIn(self.stage, qs)
        self.assertNotIn(self.inactive_stage, qs)
