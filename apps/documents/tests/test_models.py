"""Testy modelu Document aplikacji documents."""

from __future__ import annotations

import tempfile

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from apps.companies.models import Company
from apps.documents.models import Document

# Tymczasowy katalog MEDIA_ROOT dla testow plikowych
TEMP_MEDIA = tempfile.mkdtemp()


class DocumentStrTest(TestCase):
    """Testy metody __str__ modelu Document."""

    def setUp(self) -> None:
        """Tworzy firme i dokument testowy."""
        self.company = Company.objects.create(name="Acme SA")
        self.doc = Document.objects.create(
            title="Oferta Q1 2026",
            doc_type=Document.DocType.OFERTA,
            file="documents/2026/01/oferta.pdf",
            company=self.company,
        )

    def test_str_contains_title_and_type(self) -> None:
        """__str__ zawiera tytul i rodzaj dokumentu."""
        self.assertEqual(str(self.doc), "Oferta Q1 2026 [Oferta]")

    def test_str_default_type_inny(self) -> None:
        """Domyslny rodzaj to INNY."""
        doc = Document.objects.create(
            title="Plik bez typu",
            file="documents/2026/01/plik.pdf",
        )
        self.assertIn("Inny", str(doc))


class DocumentFileExtensionTest(TestCase):
    """Testy wlasciwosci file_extension."""

    def test_extension_pdf(self) -> None:
        """file_extension zwraca '.pdf' dla pliku PDF."""
        doc = Document(file="documents/2026/01/raport.pdf")
        self.assertEqual(doc.file_extension, ".pdf")

    def test_extension_docx(self) -> None:
        """file_extension zwraca '.docx' dla pliku Word."""
        doc = Document(file="documents/2026/01/umowa.docx")
        self.assertEqual(doc.file_extension, ".docx")

    def test_extension_uppercase_lowercased(self) -> None:
        """file_extension zwraca rozszerzenie pisane malymi literami."""
        doc = Document(file="documents/2026/01/SKAN.PDF")
        self.assertEqual(doc.file_extension, ".pdf")

    def test_extension_empty_when_no_file(self) -> None:
        """file_extension zwraca pusty string gdy brak pliku."""
        doc = Document()
        self.assertEqual(doc.file_extension, "")

    def test_extension_empty_when_no_suffix(self) -> None:
        """file_extension zwraca pusty string dla pliku bez rozszerzenia."""
        doc = Document(file="documents/2026/01/plik_bez_rozszerzenia")
        self.assertEqual(doc.file_extension, "")


class DocumentFileSizeDisplayTest(TestCase):
    """Testy wlasciwosci file_size_display."""

    def test_size_display_na_when_no_file(self) -> None:
        """file_size_display zwraca 'N/A' gdy brak pliku."""
        doc = Document()
        self.assertEqual(doc.file_size_display, "N/A")

    def test_size_display_na_when_file_missing_on_disk(self) -> None:
        """file_size_display zwraca 'N/A' gdy plik nie istnieje na dysku."""
        doc = Document.objects.create(
            title="Brakujacy plik",
            file="documents/nonexistent/plik.pdf",
        )
        self.assertEqual(doc.file_size_display, "N/A")

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_size_display_kb_for_small_file(self) -> None:
        """file_size_display zwraca wartosc w KB dla malych plikow."""
        doc = Document.objects.create(title="Maly plik", file="test_small.pdf")
        doc.file.save(
            "test_small.pdf",
            ContentFile(b"X" * 512),  # 512 bajtow = 0.5 KB
            save=True,
        )
        result = doc.file_size_display
        self.assertIn("KB", result)

    @override_settings(MEDIA_ROOT=TEMP_MEDIA)
    def test_size_display_mb_for_large_file(self) -> None:
        """file_size_display zwraca wartosc w MB dla duzych plikow."""
        doc = Document.objects.create(title="Duzy plik", file="test_large.pdf")
        doc.file.save(
            "test_large.pdf",
            ContentFile(b"X" * (2 * 1024 * 1024)),  # 2 MB
            save=True,
        )
        result = doc.file_size_display
        self.assertIn("MB", result)


class DocumentDefaultsAndRelationsTest(TestCase):
    """Testy wartosci domyslnych i relacji modelu Document."""

    def setUp(self) -> None:
        """Tworzy uzytkownika i firme bazowa."""
        self.user = User.objects.create_user(username="handlowiec")
        self.company = Company.objects.create(name="Beta Corp")

    def test_default_doc_type_is_inny(self) -> None:
        """Domyslny rodzaj dokumentu to INNY."""
        doc = Document.objects.create(
            title="Test",
            file="documents/2026/01/test.pdf",
        )
        self.assertEqual(doc.doc_type, Document.DocType.INNY)

    def test_all_fk_optional(self) -> None:
        """Pola company, lead, deal, created_by sa opcjonalne."""
        doc = Document.objects.create(
            title="Minimalny dokument",
            file="documents/2026/01/min.pdf",
        )
        self.assertIsNone(doc.company)
        self.assertIsNone(doc.lead)
        self.assertIsNone(doc.deal)
        self.assertIsNone(doc.created_by)

    def test_set_null_on_company_delete(self) -> None:
        """Usuniecie firmy ustawia document.company=NULL (SET_NULL)."""
        doc = Document.objects.create(
            title="Dok firmowy",
            file="documents/2026/01/firm.pdf",
            company=self.company,
        )
        self.company.delete()
        doc.refresh_from_db()
        self.assertIsNone(doc.company)

    def test_set_null_on_user_delete(self) -> None:
        """Usuniecie uzytkownika ustawia created_by=NULL (SET_NULL)."""
        doc = Document.objects.create(
            title="Dok uzytkownika",
            file="documents/2026/01/user.pdf",
            created_by=self.user,
        )
        self.user.delete()
        doc.refresh_from_db()
        self.assertIsNone(doc.created_by)

    def test_ordering_newest_first(self) -> None:
        """Dokumenty sortowane od najnowszego."""
        Document.objects.create(title="Starszy", file="documents/2026/01/a.pdf")
        Document.objects.create(title="Nowszy", file="documents/2026/01/b.pdf")
        self.assertEqual(Document.objects.first().title, "Nowszy")

    def test_doc_type_choices_count(self) -> None:
        """DocType zawiera 5 rodzajow dokumentow."""
        self.assertEqual(len(Document.DocType.choices), 5)

    def test_upload_to_path_pattern(self) -> None:
        """FileField ma skonfigurowana sciezke upload_to z data."""
        field = Document._meta.get_field("file")
        self.assertEqual(field.upload_to, "documents/%Y/%m/")
