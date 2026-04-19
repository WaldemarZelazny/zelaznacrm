"""Testy widokow CRUD i pobierania plikow aplikacji documents."""

from __future__ import annotations

import tempfile

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.deals.models import Deal
from apps.documents.models import Document
from apps.leads.models import Lead, WorkflowStage

# Tymczasowy katalog MEDIA_ROOT dla testow wgrywania plikow
TEMP_MEDIA = tempfile.mkdtemp()

# ---------------------------------------------------------------------------
# Pomocnicze funkcje
# ---------------------------------------------------------------------------


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    """Tworzy uzytkownika z profilem o podanej roli."""
    user = User.objects.create_user(username=username, password="testpass")
    user.profile.role = role
    user.profile.save()
    return user


def _make_company(name: str, owner: User | None = None) -> Company:
    """Tworzy firme testowa."""
    return Company.objects.create(name=name, owner=owner)


def _make_document(
    title: str,
    created_by: User | None = None,
    company: Company | None = None,
    doc_type: str = Document.DocType.INNY,
) -> Document:
    """Tworzy dokument testowy (z atrapowym sciezka pliku)."""
    return Document.objects.create(
        title=title,
        doc_type=doc_type,
        file="documents/2026/01/test.pdf",
        company=company,
        created_by=created_by,
    )


def _make_lead(title: str, company: Company, owner: User | None = None) -> Lead:
    """Tworzy lead testowy."""
    stage, _ = WorkflowStage.objects.get_or_create(
        order=1, defaults={"name": "Nowy", "color": "#6c757d"}
    )
    return Lead.objects.create(title=title, company=company, owner=owner, stage=stage)


def _make_deal(title: str, company: Company, owner: User | None = None) -> Deal:
    """Tworzy umowe testowa."""
    import datetime

    return Deal.objects.create(
        title=title,
        company=company,
        owner=owner,
        value="5000.00",
        close_date=datetime.date.today() + datetime.timedelta(days=30),
    )


def _pdf_file(name: str = "test.pdf") -> SimpleUploadedFile:
    """Zwraca prosty obiekt SimpleUploadedFile symulujacy PDF."""
    return SimpleUploadedFile(
        name, b"%PDF-1.4 fake content", content_type="application/pdf"
    )


# ---------------------------------------------------------------------------
# Testy: przekierowanie niezalogowanych
# ---------------------------------------------------------------------------


class DocumentViewsAuthRedirectTest(TestCase):
    """Niezalogowani uzytkowniczy musza byc przekierowani na login."""

    def setUp(self) -> None:
        self.user = _make_user("auth_user")
        self.company = _make_company("Auth Co", owner=self.user)
        self.doc = _make_document(
            "Auth doc", created_by=self.user, company=self.company
        )

    def _assert_redirects_to_login(self, url: str, method: str = "get") -> None:
        response = getattr(self.client, method)(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_list_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("documents:list"))

    def test_detail_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("documents:detail", kwargs={"pk": self.doc.pk})
        )

    def test_create_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("documents:create"))

    def test_update_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("documents:update", kwargs={"pk": self.doc.pk})
        )

    def test_delete_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("documents:delete", kwargs={"pk": self.doc.pk})
        )

    def test_download_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("documents:download", kwargs={"pk": self.doc.pk})
        )


# ---------------------------------------------------------------------------
# Testy: DocumentListView
# ---------------------------------------------------------------------------


class DocumentListViewTest(TestCase):
    """Testy widoku listy dokumentow."""

    def setUp(self) -> None:
        self.admin = _make_user("list_admin", role=UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("list_handlowiec")
        self.company = _make_company("List Co", owner=self.handlowiec)
        self.own_doc = _make_document(
            "Moj dokument",
            created_by=self.handlowiec,
            company=self.company,
        )
        self.other_doc = _make_document(
            "Cudzy dokument",
            created_by=self.admin,
            company=self.company,
        )

    def test_list_returns_200(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("documents:list"))
        self.assertEqual(response.status_code, 200)

    def test_admin_sees_all_documents(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("documents:list"))
        docs = list(response.context["documents"])
        self.assertIn(self.own_doc, docs)
        self.assertIn(self.other_doc, docs)

    def test_handlowiec_sees_only_own_documents(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("documents:list"))
        docs = list(response.context["documents"])
        self.assertIn(self.own_doc, docs)
        self.assertNotIn(self.other_doc, docs)

    def test_filter_by_doc_type(self) -> None:
        oferta = _make_document(
            "Oferta specjalna",
            created_by=self.handlowiec,
            company=self.company,
            doc_type=Document.DocType.OFERTA,
        )
        self.client.force_login(self.handlowiec)
        response = self.client.get(
            reverse("documents:list"), {"doc_type": Document.DocType.OFERTA}
        )
        docs = list(response.context["documents"])
        self.assertIn(oferta, docs)
        self.assertNotIn(self.own_doc, docs)

    def test_context_has_doc_type_choices(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("documents:list"))
        self.assertIn("doc_type_choices", response.context)
        self.assertTrue(len(response.context["doc_type_choices"]) > 0)


# ---------------------------------------------------------------------------
# Testy: DocumentDetailView
# ---------------------------------------------------------------------------


class DocumentDetailViewTest(TestCase):
    """Testy widoku szczegolowego dokumentu."""

    def setUp(self) -> None:
        self.creator = _make_user("detail_creator")
        self.other = _make_user("detail_other")
        self.admin = _make_user("detail_admin", role=UserProfile.Role.ADMIN)
        self.company = _make_company("Detail Co", owner=self.creator)
        self.doc = _make_document(
            "Detail doc", created_by=self.creator, company=self.company
        )

    def test_creator_can_view_document(self) -> None:
        self.client.force_login(self.creator)
        response = self.client.get(
            reverse("documents:detail", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_any_document(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("documents:detail", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_404(self) -> None:
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("documents:detail", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_context_has_can_edit_true_for_creator(self) -> None:
        self.client.force_login(self.creator)
        response = self.client.get(
            reverse("documents:detail", kwargs={"pk": self.doc.pk})
        )
        self.assertTrue(response.context["can_edit"])

    def test_context_has_is_admin_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("documents:detail", kwargs={"pk": self.doc.pk})
        )
        self.assertTrue(response.context["is_admin"])


# ---------------------------------------------------------------------------
# Testy: DocumentCreateView
# ---------------------------------------------------------------------------


class DocumentCreateViewTest(TestCase):
    """Testy widoku tworzenia dokumentu."""

    def setUp(self) -> None:
        self.user = _make_user("create_user")
        self.company = _make_company("Create Co", owner=self.user)

    def test_create_get_returns_200(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:create"))
        self.assertEqual(response.status_code, 200)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_create_document_success(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("documents:create"),
            {
                "title": "Nowy dokument",
                "doc_type": Document.DocType.OFERTA,
                "file": _pdf_file(),
            },
        )
        self.assertEqual(Document.objects.filter(title="Nowy dokument").count(), 1)
        doc = Document.objects.get(title="Nowy dokument")
        self.assertRedirects(
            response, reverse("documents:detail", kwargs={"pk": doc.pk})
        )

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_create_sets_created_by(self) -> None:
        self.client.force_login(self.user)
        self.client.post(
            reverse("documents:create"),
            {
                "title": "Dok z created_by",
                "doc_type": Document.DocType.UMOWA,
                "file": _pdf_file("umowa.pdf"),
            },
        )
        doc = Document.objects.get(title="Dok z created_by")
        self.assertEqual(doc.created_by, self.user)

    def test_create_prefill_company_id(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("documents:create"), {"company_id": self.company.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("company"), self.company)

    def test_create_prefill_lead_id(self) -> None:
        lead = _make_lead("Lead prefill", self.company, owner=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:create"), {"lead_id": lead.pk})
        self.assertEqual(response.status_code, 200)
        initial = response.context["form"].initial
        self.assertEqual(initial.get("lead"), lead)

    def test_create_prefill_deal_id(self) -> None:
        deal = _make_deal("Deal prefill", self.company, owner=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:create"), {"deal_id": deal.pk})
        self.assertEqual(response.status_code, 200)
        initial = response.context["form"].initial
        self.assertEqual(initial.get("deal"), deal)


# ---------------------------------------------------------------------------
# Testy: DocumentUpdateView
# ---------------------------------------------------------------------------


class DocumentUpdateViewTest(TestCase):
    """Testy widoku edycji dokumentu."""

    def setUp(self) -> None:
        self.creator = _make_user("update_creator")
        self.other = _make_user("update_other")
        self.admin = _make_user("update_admin", role=UserProfile.Role.ADMIN)
        self.company = _make_company("Update Co", owner=self.creator)
        self.doc = _make_document(
            "Update doc", created_by=self.creator, company=self.company
        )

    def test_creator_can_edit(self) -> None:
        self.client.force_login(self.creator)
        response = self.client.get(
            reverse("documents:update", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_edit_any_document(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("documents:update", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_403(self) -> None:
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("documents:update", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_update_document_success(self) -> None:
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("documents:update", kwargs={"pk": self.doc.pk}),
            {
                "title": "Zaktualizowany dokument",
                "doc_type": Document.DocType.UMOWA,
            },
        )
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.title, "Zaktualizowany dokument")
        self.assertRedirects(
            response, reverse("documents:detail", kwargs={"pk": self.doc.pk})
        )


# ---------------------------------------------------------------------------
# Testy: DocumentDeleteView
# ---------------------------------------------------------------------------


class DocumentDeleteViewTest(TestCase):
    """Testy widoku usuwania dokumentu (tylko ADMIN)."""

    def setUp(self) -> None:
        self.admin = _make_user("delete_admin", role=UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("delete_handlowiec")
        self.company = _make_company("Delete Co", owner=self.handlowiec)
        self.doc = _make_document(
            "Delete doc", created_by=self.handlowiec, company=self.company
        )

    def test_admin_can_delete(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("documents:delete", kwargs={"pk": self.doc.pk})
        )
        self.assertFalse(Document.objects.filter(pk=self.doc.pk).exists())
        self.assertRedirects(response, reverse("documents:list"))

    def test_handlowiec_gets_403_on_delete(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.post(
            reverse("documents:delete", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Document.objects.filter(pk=self.doc.pk).exists())

    def test_delete_confirm_page_returns_200_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("documents:delete", kwargs={"pk": self.doc.pk})
        )
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Testy: DocumentDownloadView
# ---------------------------------------------------------------------------


class DocumentDownloadViewTest(TestCase):
    """Testy widoku pobierania pliku dokumentu."""

    def setUp(self) -> None:
        self.user = _make_user("download_user")
        self.other = _make_user("download_other")
        self.company = _make_company("Download Co", owner=self.user)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_download_returns_200(self) -> None:
        """Zalogowany uzytkownik moze pobrac dowolny dokument."""
        doc = Document.objects.create(
            title="Pobierz mnie",
            created_by=self.user,
        )
        doc.file.save("pobierz.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:download", kwargs={"pk": doc.pk}))
        self.assertEqual(response.status_code, 200)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_download_as_attachment(self) -> None:
        """Odpowiedz zawiera naglowek Content-Disposition z 'attachment'."""
        doc = Document.objects.create(title="Zalacznik", created_by=self.user)
        doc.file.save("zalacznik.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:download", kwargs={"pk": doc.pk}))
        self.assertIn("attachment", response.get("Content-Disposition", ""))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_download_correct_filename_in_header(self) -> None:
        """Naglowek Content-Disposition zawiera nazwe pliku."""
        doc = Document.objects.create(title="Raport", created_by=self.user)
        doc.file.save("raport_q1.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:download", kwargs={"pk": doc.pk}))
        self.assertIn("raport_q1.pdf", response.get("Content-Disposition", ""))

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_download_returns_file_content(self) -> None:
        """Pobrane dane zawieraja oczekiwana zawartosc pliku."""
        content = b"%PDF-1.4 expected content"
        doc = Document.objects.create(title="Content doc", created_by=self.user)
        doc.file.save("content.pdf", ContentFile(content), save=True)
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:download", kwargs={"pk": doc.pk}))
        # FileResponse jest strumieniowe — laczymy fragmenty
        downloaded = b"".join(response.streaming_content)
        self.assertEqual(downloaded, content)

    def test_download_missing_file_returns_404(self) -> None:
        """Dokument z nieistniejacym plikiem zwraca 404."""
        doc = Document.objects.create(
            title="Brakujacy plik",
            file="documents/nonexistent/brak.pdf",
            created_by=self.user,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("documents:download", kwargs={"pk": doc.pk}))
        self.assertEqual(response.status_code, 404)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_download_accessible_by_other_logged_user(self) -> None:
        """Inny zalogowany uzytkownik (nie tworca) tez moze pobrac plik."""
        doc = Document.objects.create(title="Publiczny", created_by=self.user)
        doc.file.save("publiczny.pdf", ContentFile(b"%PDF test"), save=True)
        self.client.force_login(self.other)
        response = self.client.get(reverse("documents:download", kwargs={"pk": doc.pk}))
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# DocumentPDFView
# ---------------------------------------------------------------------------

import sys  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

PDF_URL = "documents:pdf"
_MOCK_PDF_BYTES = b"%PDF-1.4 mock-pdf-content"


def _weasyprint_patch():
    """Zwraca patch zastepujacy modul WeasyPrint falszywymi bajtami PDF.

    WeasyPrint wymaga bibliotek systemowych GTK (libgobject), ktore nie sa
    dostepne w tym srodowisku Windows. Import jest leniwy w widoku, wiec
    wstrzykujemy mock do sys.modules przed kazda probą importu.
    """
    mock_wp = MagicMock()
    mock_wp.HTML.return_value.write_pdf.return_value = _MOCK_PDF_BYTES
    return __import__("unittest.mock", fromlist=["patch"]).patch.dict(
        sys.modules, {"weasyprint": mock_wp}
    )


class DocumentPDFAuthTest(TestCase):
    """Testy uwierzytelniania DocumentPDFView."""

    def setUp(self) -> None:
        self.user = _make_user("pdf_user")
        self.doc = _make_document("Karta PDF", created_by=self.user)

    def test_pdf_redirect_anonymous(self) -> None:
        """Anonimowy uzytkownik jest przekierowywany do logowania."""
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": self.doc.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_pdf_returns_403_for_other_user(self) -> None:
        """Inny handlowiec (nie tworca) otrzymuje 403."""
        other = _make_user("pdf_other")
        self.client.force_login(other)
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": self.doc.pk}))
        self.assertEqual(response.status_code, 403)


class DocumentPDFGenerateTest(TestCase):
    """Testy generowania PDF przez DocumentPDFView."""

    def setUp(self) -> None:
        self.user = _make_user("pdf_gen")
        self.admin = _make_user("pdf_admin", role=UserProfile.Role.ADMIN)
        self.doc = _make_document("Oferta Testowa", created_by=self.user)

    def test_pdf_returns_200_for_creator(self) -> None:
        """Tworca dokumentu otrzymuje odpowiedz 200."""
        self.client.force_login(self.user)
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": self.doc.pk}))
        self.assertEqual(response.status_code, 200)

    def test_pdf_content_type(self) -> None:
        """Odpowiedz ma Content-Type application/pdf."""
        self.client.force_login(self.user)
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": self.doc.pk}))
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_pdf_content_disposition_is_attachment(self) -> None:
        """Odpowiedz zawiera naglowek Content-Disposition z attachment."""
        self.client.force_login(self.user)
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": self.doc.pk}))
        self.assertIn("attachment", response["Content-Disposition"])

    def test_pdf_returns_pdf_bytes(self) -> None:
        """Tresc odpowiedzi zaczyna sie od sygnatury %PDF (mock)."""
        self.client.force_login(self.user)
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": self.doc.pk}))
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_pdf_accessible_by_admin(self) -> None:
        """ADMIN moze pobrac PDF dowolnego dokumentu."""
        self.client.force_login(self.admin)
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": self.doc.pk}))
        self.assertEqual(response.status_code, 200)

    def test_pdf_returns_404_for_nonexistent(self) -> None:
        """Nieistniejacy dokument zwraca 404."""
        self.client.force_login(self.admin)
        with _weasyprint_patch():
            response = self.client.get(reverse(PDF_URL, kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)
