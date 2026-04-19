"""Testy formularzy aplikacji deals."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.deals.forms import DealForm
from apps.leads.models import Lead, WorkflowStage


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    user = User.objects.create_user(username=username, password="pass")
    user.profile.role = role
    user.profile.save()
    return user


def _make_company(name: str, owner: User) -> Company:
    return Company.objects.create(name=name, owner=owner)


def _make_stage(name: str = "Kwalifikacja", order: int = 1) -> WorkflowStage:
    return WorkflowStage.objects.create(name=name, order=order, is_active=True)


def _make_lead(title: str, company: Company, owner: User) -> Lead:
    stage = WorkflowStage.objects.filter(is_active=True).first() or _make_stage()
    return Lead.objects.create(title=title, company=company, owner=owner, stage=stage)


class DealFormTest(TestCase):
    def setUp(self):
        self.admin = _make_user("admin", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec")
        self.own_company = _make_company("Własna Sp. z o.o.", self.handlowiec)
        self.other_company = _make_company("Obca Sp. z o.o.", self.admin)
        self.own_lead = _make_lead("Mój lead", self.own_company, self.handlowiec)
        self.other_lead = _make_lead("Obcy lead", self.other_company, self.admin)

    def _valid_data(self, **overrides) -> dict:
        data = {
            "title": "Umowa testowa",
            "company": self.own_company.pk,
            "lead": "",
            "value": "10000.00",
            "close_date": "2026-12-31",
            "description": "",
        }
        data.update(overrides)
        return data

    # --- Poprawne dane ---

    def test_valid_data_is_valid(self):
        form = DealForm(data=self._valid_data(), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_lead_is_valid(self):
        form = DealForm(
            data=self._valid_data(lead=self.own_lead.pk), user=self.handlowiec
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Brakujące wymagane pola ---

    def test_missing_title_invalid(self):
        form = DealForm(data=self._valid_data(title=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_missing_company_invalid(self):
        form = DealForm(data=self._valid_data(company=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    def test_missing_close_date_invalid(self):
        form = DealForm(data=self._valid_data(close_date=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("close_date", form.errors)

    def test_invalid_date_format_invalid(self):
        form = DealForm(
            data=self._valid_data(close_date="31-12-2026"), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("close_date", form.errors)

    def test_lead_optional(self):
        form = DealForm(data=self._valid_data(lead=""), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_description_optional(self):
        form = DealForm(data=self._valid_data(description=""), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    # --- Dynamiczny queryset: company ---

    def test_handlowiec_sees_only_own_companies(self):
        form = DealForm(user=self.handlowiec)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertNotIn(self.other_company, qs)

    def test_admin_sees_all_companies(self):
        form = DealForm(user=self.admin)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertIn(self.other_company, qs)

    def test_handlowiec_cannot_assign_foreign_company(self):
        form = DealForm(
            data=self._valid_data(company=self.other_company.pk), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    def test_admin_can_assign_any_company(self):
        form = DealForm(
            data=self._valid_data(company=self.other_company.pk), user=self.admin
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Dynamiczny queryset: lead ---

    def test_handlowiec_sees_only_own_leads(self):
        form = DealForm(user=self.handlowiec)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertNotIn(self.other_lead, qs)

    def test_admin_sees_all_leads(self):
        form = DealForm(user=self.admin)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertIn(self.other_lead, qs)

    def test_handlowiec_cannot_assign_foreign_lead(self):
        form = DealForm(
            data=self._valid_data(lead=self.other_lead.pk), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("lead", form.errors)
