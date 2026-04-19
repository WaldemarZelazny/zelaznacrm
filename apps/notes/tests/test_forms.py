"""Testy formularzy aplikacji notes."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage
from apps.notes.forms import NoteForm


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


def _make_stage() -> WorkflowStage:
    return WorkflowStage.objects.create(name="Kwalifikacja", order=1, is_active=True)


def _make_lead(title: str, company: Company, owner: User) -> Lead:
    stage = WorkflowStage.objects.filter(is_active=True).first() or _make_stage()
    return Lead.objects.create(title=title, company=company, owner=owner, stage=stage)


def _make_deal(title: str, company: Company, owner: User) -> Deal:
    return Deal.objects.create(
        title=title, company=company, owner=owner, close_date="2026-12-31"
    )


class NoteFormTest(TestCase):
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
        self.own_lead = _make_lead("Mój lead", self.own_company, self.handlowiec)
        self.other_lead = _make_lead("Obcy lead", self.other_company, self.admin)
        self.own_deal = _make_deal("Moja umowa", self.own_company, self.handlowiec)
        self.other_deal = _make_deal("Obca umowa", self.other_company, self.admin)

    def _valid_data(self, **overrides) -> dict:
        data = {
            "content": "Treść testowej notatki.",
            "company": "",
            "lead": "",
            "deal": "",
            "contact": "",
        }
        data.update(overrides)
        return data

    # --- Poprawne dane ---

    def test_valid_data_is_valid(self):
        form = NoteForm(data=self._valid_data(), user=self.handlowiec)
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_all_links(self):
        form = NoteForm(
            data=self._valid_data(
                company=self.own_company.pk,
                lead=self.own_lead.pk,
                deal=self.own_deal.pk,
                contact=self.own_contact.pk,
            ),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Brakujące wymagane pola ---

    def test_missing_content_invalid(self):
        form = NoteForm(data=self._valid_data(content=""), user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    # --- Wszystkie linki opcjonalne ---

    def test_all_links_optional(self):
        form = NoteForm(
            data=self._valid_data(company="", lead="", deal="", contact=""),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Dynamiczny queryset: company ---

    def test_handlowiec_sees_only_own_companies(self):
        form = NoteForm(user=self.handlowiec)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertNotIn(self.other_company, qs)

    def test_admin_sees_all_companies(self):
        form = NoteForm(user=self.admin)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertIn(self.other_company, qs)

    def test_handlowiec_cannot_assign_foreign_company(self):
        form = NoteForm(
            data=self._valid_data(company=self.other_company.pk),
            user=self.handlowiec,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    # --- Dynamiczny queryset: contact ---

    def test_handlowiec_sees_contacts_from_own_companies(self):
        form = NoteForm(user=self.handlowiec)
        qs = form.fields["contact"].queryset
        self.assertIn(self.own_contact, qs)
        self.assertNotIn(self.other_contact, qs)

    def test_admin_sees_all_contacts(self):
        form = NoteForm(user=self.admin)
        qs = form.fields["contact"].queryset
        self.assertIn(self.own_contact, qs)
        self.assertIn(self.other_contact, qs)

    # --- Dynamiczny queryset: lead ---

    def test_handlowiec_sees_only_own_leads(self):
        form = NoteForm(user=self.handlowiec)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertNotIn(self.other_lead, qs)

    def test_admin_sees_all_leads(self):
        form = NoteForm(user=self.admin)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertIn(self.other_lead, qs)

    # --- Dynamiczny queryset: deal ---

    def test_handlowiec_sees_only_own_deals(self):
        form = NoteForm(user=self.handlowiec)
        qs = form.fields["deal"].queryset
        self.assertIn(self.own_deal, qs)
        self.assertNotIn(self.other_deal, qs)

    def test_admin_sees_all_deals(self):
        form = NoteForm(user=self.admin)
        qs = form.fields["deal"].queryset
        self.assertIn(self.own_deal, qs)
        self.assertIn(self.other_deal, qs)
