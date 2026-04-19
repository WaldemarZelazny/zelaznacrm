"""Testy formularzy aplikacji documents."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.deals.models import Deal
from apps.documents.forms import DocumentForm
from apps.documents.models import Document
from apps.leads.models import Lead, WorkflowStage


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


def _make_document(title: str, owner: User) -> Document:
    f = SimpleUploadedFile("doc.txt", b"content", content_type="text/plain")
    return Document.objects.create(title=title, file=f, created_by=owner)


def _mock_file(name: str = "test.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"%PDF-1.4 mock", content_type="application/pdf")


class DocumentFormCreateTest(TestCase):
    """Testy formularza przy tworzeniu (bez instance → file wymagany)."""

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
            "title": "Testowy dokument",
            "doc_type": Document.DocType.INNY,
            "company": "",
            "lead": "",
            "deal": "",
            "description": "",
        }
        data.update(overrides)
        return data

    def _valid_files(self, file=None) -> dict:
        return {"file": file or _mock_file()}

    # --- Poprawne dane ---

    def test_valid_data_with_file_is_valid(self):
        form = DocumentForm(
            data=self._valid_data(), files=self._valid_files(), user=self.handlowiec
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_company_link(self):
        form = DocumentForm(
            data=self._valid_data(company=self.own_company.pk),
            files=self._valid_files(),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Brakujące wymagane pola ---

    def test_missing_title_invalid(self):
        form = DocumentForm(
            data=self._valid_data(title=""),
            files=self._valid_files(),
            user=self.handlowiec,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_file_required_on_create(self):
        form = DocumentForm(data=self._valid_data(), files={}, user=self.handlowiec)
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_invalid_doc_type_invalid(self):
        form = DocumentForm(
            data=self._valid_data(doc_type="NIEZNANY"),
            files=self._valid_files(),
            user=self.handlowiec,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("doc_type", form.errors)

    # --- Pola opcjonalne ---

    def test_all_crm_links_optional(self):
        form = DocumentForm(
            data=self._valid_data(company="", lead="", deal=""),
            files=self._valid_files(),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_description_optional(self):
        form = DocumentForm(
            data=self._valid_data(description=""),
            files=self._valid_files(),
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Dynamiczny queryset: company ---

    def test_handlowiec_sees_only_own_companies(self):
        form = DocumentForm(user=self.handlowiec)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertNotIn(self.other_company, qs)

    def test_admin_sees_all_companies(self):
        form = DocumentForm(user=self.admin)
        qs = form.fields["company"].queryset
        self.assertIn(self.own_company, qs)
        self.assertIn(self.other_company, qs)

    def test_handlowiec_cannot_assign_foreign_company(self):
        form = DocumentForm(
            data=self._valid_data(company=self.other_company.pk),
            files=self._valid_files(),
            user=self.handlowiec,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("company", form.errors)

    # --- Dynamiczny queryset: lead / deal ---

    def test_handlowiec_sees_only_own_leads(self):
        form = DocumentForm(user=self.handlowiec)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertNotIn(self.other_lead, qs)

    def test_handlowiec_sees_only_own_deals(self):
        form = DocumentForm(user=self.handlowiec)
        qs = form.fields["deal"].queryset
        self.assertIn(self.own_deal, qs)
        self.assertNotIn(self.other_deal, qs)

    def test_admin_sees_all_leads(self):
        form = DocumentForm(user=self.admin)
        qs = form.fields["lead"].queryset
        self.assertIn(self.own_lead, qs)
        self.assertIn(self.other_lead, qs)


class DocumentFormUpdateTest(TestCase):
    """Testy formularza przy edycji (instance istnieje → file opcjonalny)."""

    def setUp(self):
        self.handlowiec = _make_user("handlowiec")
        self.document = _make_document("Istniejący dokument", self.handlowiec)

    def _valid_data(self, **overrides) -> dict:
        data = {
            "title": "Zaktualizowany dokument",
            "doc_type": Document.DocType.OFERTA,
            "company": "",
            "lead": "",
            "deal": "",
            "description": "Nowy opis",
        }
        data.update(overrides)
        return data

    def test_file_optional_on_update(self):
        form = DocumentForm(
            data=self._valid_data(),
            files={},
            instance=self.document,
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_update_with_new_file_is_valid(self):
        form = DocumentForm(
            data=self._valid_data(),
            files={"file": _mock_file("nowy.pdf")},
            instance=self.document,
            user=self.handlowiec,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_file_required_true_on_new_form(self):
        form = DocumentForm(user=self.handlowiec)
        self.assertTrue(form.fields["file"].required)

    def test_file_required_false_on_edit_form(self):
        form = DocumentForm(instance=self.document, user=self.handlowiec)
        self.assertFalse(form.fields["file"].required)
