"""Modele aplikacji documents – dokumenty i pliki CRM."""

from __future__ import annotations

import logging
from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead

logger = logging.getLogger(__name__)

# Progi dla czytelnego wyswietlania rozmiarow plikow
_KB = 1024
_MB = 1024 * _KB


class Document(models.Model):
    """Dokument lub plik powiazany z firma, leadem lub umowa.

    Przechowuje referencje do plikow (PDF, DOCX itp.) wgrywanych
    przez handlowcow. Jeden dokument nalezy do jednego kontekstu
    biznesowego (oferta, umowa, protokol), ale moze byc jednoczesnie
    powiazany z firma, leadem i umowa.

    Attributes:
        title: Nazwa / tytul dokumentu widoczny w interfejsie.
        doc_type: Rodzaj dokumentu (TextChoices).
        file: Wgrany plik – sciezka wzgledna wzgledem MEDIA_ROOT.
        company: Powiazana firma (opcjonalna, FK SET_NULL).
        lead: Powiazany lead (opcjonalny, FK SET_NULL).
        deal: Powiazana umowa (opcjonalna, FK SET_NULL).
        created_by: Uzytkownik ktory wgral dokument (FK SET_NULL).
        description: Opcjonalny opis / komentarz do dokumentu.
        created_at: Data wgrania dokumentu (automatyczna).
        updated_at: Data ostatniej modyfikacji metadanych (automatyczna).
    """

    class DocType(models.TextChoices):
        """Rodzaj dokumentu CRM."""

        OFERTA = "OFERTA", _("Oferta")
        UMOWA = "UMOWA", _("Umowa")
        PROTOKOL = "PROTOKOL", _("Protokol odbioru")
        FAKTURA = "FAKTURA", _("Faktura")
        INNY = "INNY", _("Inny")

    title = models.CharField(
        max_length=200,
        verbose_name=_("tytul dokumentu"),
    )
    doc_type = models.CharField(
        max_length=20,
        choices=DocType,
        default=DocType.INNY,
        verbose_name=_("rodzaj dokumentu"),
    )
    file = models.FileField(
        upload_to="documents/%Y/%m/",
        verbose_name=_("plik"),
        help_text=_("Dozwolone formaty: PDF, DOCX, XLSX, JPG, PNG."),
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("firma"),
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("lead"),
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name=_("umowa"),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
        verbose_name=_("wgrane przez"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("opis"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("data wgrania"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("data modyfikacji"),
    )

    class Meta:
        verbose_name = _("dokument")
        verbose_name_plural = _("dokumenty")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Zwraca tytul dokumentu z rodzajem w nawiasie."""
        return f"{self.title} [{self.get_doc_type_display()}]"

    # ------------------------------------------------------------------
    # Wlasciwosci
    # ------------------------------------------------------------------

    @property
    def file_extension(self) -> str:
        """Zwraca rozszerzenie pliku (z kropka, np. '.pdf').

        Returns:
            Rozszerzenie pliku pisane malymi literami lub pusty string
            gdy plik nie istnieje lub nie ma rozszerzenia.
        """
        if not self.file:
            return ""
        return Path(self.file.name).suffix.lower()

    @property
    def file_size_display(self) -> str:
        """Zwraca rozmiar pliku w czytelnym formacie (KB lub MB).

        Probuje odczytac rozmiar pliku ze storage. Gdy plik nie
        istnieje lub wystapi blad I/O, zwraca 'N/A'.

        Returns:
            Sformatowany rozmiar np. '245.3 KB' lub '1.8 MB',
            albo 'N/A' gdy plik niedostepny.
        """
        if not self.file:
            return "N/A"
        try:
            size = self.file.size
        except (FileNotFoundError, OSError):
            return "N/A"

        if size >= _MB:
            return f"{size / _MB:.1f} MB"
        return f"{size / _KB:.1f} KB"
