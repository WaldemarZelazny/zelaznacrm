"""Testy formularzy aplikacji tasks."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage
from apps.tasks.forms import TaskForm
from apps.tasks.models import Task


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    user = User.objects.create_user(username=username, password="pass")
    user.profile.role = role
    user.profile.save()
    return user


def _make_company(name: str, owner: User) -> Company:
    return Company.objects.create(name=name, owner=owner)


def _make_stage() -> WorkflowStage:
    return WorkflowStage.objects.create(name="Kwalifikacja", order=1, is_active=True)


def _make_lead(title: str, company: Company, owner: User) -> Lead:
    stage = WorkflowStage.objects.filter(is_active=True).first() or _make_stage()
    return Lead.objects.create(title=title, company=company, owner=owner, stage=stage)


def _make_deal(title: str, company: Company, owner: User) -> Deal:
    return Deal.objects.create(
        title=title, company=company, owner=owner, close_date="2026-12-31"
    )


class TaskFormTest(TestCase):
    def setUp(self):
        self.admin = _make_user("admin", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec")
        self.own_company = _make_company("Własna Sp. z o.o.", self.handlowiec)
        self.other_company = _make_company("Obca Sp. z o.o.", self.admin)
        self.own_lead = _make_lead("Mój lead", self.own_company, self.handlowiec)
        self.other_lead = _make_lead("Obcy lead", self.other_company, self.admin)
        self.own_deal = _make_deal("Moja umowa", self.own_company, self.handlowiec)
        self.other_deal = _make_deal("Obca umowa", self.other_company, self.admin)

    def _valid_data(self, **overrides) -> dict:
        data = {
            "title": "Testowe zadanie",
            "task_type": Task.TaskType.ZADANIE,
            "priority": Task.Priority.SREDNI,
            "status": Task.Status.DO_ZROBIENIA,
            "due_date": "2026-12-31T10:00",
            "assigned_to": "",
            "company": "",
            "lead": "",
            "deal": "",
            "description": "",
        }
        data.update(overrides)
        return data

    # --- Poprawne dane ---

    def test_valid_data_is_valid(self):
        form = TaskForm(data=self._valid_data(), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_assigned_user_is_valid(self):
        form = TaskForm(
            data=self._valid_data(assigned_to=self.handlowiec.pk),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_company_link(self):
        form = TaskForm(
            data=self._valid_data(company=self.own_company.pk), user=self.handlowiec
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_lead_link(self):
        form = TaskForm(
            data=self._valid_data(lead=self.own_lead.pk), user=self.handlowiec
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_deal_link(self):
        form = TaskForm(
            data=self._valid_data(deal=self.own_deal.pk), user=self.handlowiec
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Brakujące wymagane pola ---

    def test_missing_title_invalid(self):
        form = TaskForm(data=self._valid_data(title=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_invalid_task_type_invalid(self):
        form = TaskForm(
            data=self._valid_data(task_type="NIEZNANY"), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("task_type", form.errors)

    def test_invalid_priority_invalid(self):
        form = TaskForm(
            data=self._valid_data(priority="NIEZNANY"), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("priority", form.errors)

    def test_invalid_status_invalid(self):
        form = TaskForm(data=self._valid_data(status="NIEZNANY"), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)

    # --- Pola opcjonalne ---

    def test_invalid_due_date_format_invalid(self):
        form = TaskForm(
            data=self._valid_data(due_date="31-12-2026"), user=self.handlowiec
        )
        self.assertFalse(form.is_valid())
        self.assertIn("due_date", form.errors)

    def test_assigned_to_optional(self):
        form = TaskForm(data=self._valid_data(assigned_to=""), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_all_crm_links_optional(self):
        form = TaskForm(
            data=self._valid_data(company="", lead="", deal=""),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- assigned_to: wszyscy aktywni użytkownicy ---

    def test_assigned_to_includes_admin(self):
        form = TaskForm(user=self.handlowiec)
        qs = form.fields["assigned_to"].queryset
        self.assertIn(self.admin, qs)
        self.assertIn(self.handlowiec, qs)

    def test_assigned_to_excludes_inactive_user(self):
        inactive = User.objects.create_user(
            username="nieaktywny", password="pass", is_active=False
        )
        form = TaskForm(user=self.handlowiec)
        qs = form.fields["assigned_to"].queryset
        self.assertNotIn(inactive, qs)

    # --- Dynamiczny queryset: company ---

    def test_handlowiec_sees_only_own_companies(self):
        form = TaskForm(user=self.handlowiec)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertNotIn(self.other_company, qs)

    def test_admin_sees_all_companies(self):
        form = TaskForm(user=self.admin)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertIn(self.other_company, qs)

    # --- Dynamiczny queryset: lead ---

    def test_handlowiec_sees_only_own_leads(self):
        form = TaskForm(user=self.handlowiec)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertNotIn(self.other_lead, qs)

    def test_admin_sees_all_leads(self):
        form = TaskForm(user=self.admin)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertIn(self.other_lead, qs)

    # --- Dynamiczny queryset: deal ---

    def test_handlowiec_sees_only_own_deals(self):
        form = TaskForm(user=self.handlowiec)
        qs = form.fields["deal"].queryset
        self.assertIn(self.own_deal, qs)
        self.assertNotIn(self.other_deal, qs)

    def test_admin_sees_all_deals(self):
        form = TaskForm(user=self.admin)
        qs = form.fields["deal"].queryset
        self.assertIn(self.own_deal, qs)
        self.assertIn(self.other_deal, qs)
