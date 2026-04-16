"""Modele aplikacji companies – firmy i klienci systemu ZelaznaCRM."""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class Company(models.Model):
    """Firma lub klient indywidualny w systemie CRM.

    Centralny model CRM – większość innych obiektów (kontakty, leady,
    umowy, zadania) powiązana jest z firmą. Każda firma ma przypisanego
    opiekuna handlowego (ForeignKey → User).

    Attributes:
        name: Nazwa firmy lub klienta indywidualnego.
        nip: Numer Identyfikacji Podatkowej (unikalny, opcjonalny).
        industry: Branża działalności (wybór z listy).
        address: Adres siedziby.
        city: Miasto siedziby.
        postal_code: Kod pocztowy.
        phone: Główny numer telefonu.
        email: Adres e-mail firmy.
        website: Adres strony www (opcjonalny).
        owner: Opiekun handlowy (FK → User).
        notes: Dodatkowe uwagi o firmie.
        is_active: Czy firma jest aktywna w systemie.
        created_at: Data dodania firmy (automatyczna).
        updated_at: Data ostatniej modyfikacji (automatyczna).
    """

    class Industry(models.TextChoices):
        """Branże działalności firmy."""

        BUDOWNICTWO = "BUDOWNICTWO", _("Budownictwo")
        IT = "IT", _("IT / Technologia")
        HANDEL = "HANDEL", _("Handel")
        PRODUKCJA = "PRODUKCJA", _("Produkcja")
        USLUGI = "USLUGI", _("Usługi")
        FINANSE = "FINANSE", _("Finanse / Ubezpieczenia")
        TRANSPORT = "TRANSPORT", _("Transport / Logistyka")
        ZDROWIE = "ZDROWIE", _("Zdrowie / Medycyna")
        EDUKACJA = "EDUKACJA", _("Edukacja")
        INNE = "INNE", _("Inne")

    name = models.CharField(
        max_length=200,
        verbose_name=_("nazwa firmy"),
        help_text=_("Pełna nazwa firmy lub imię i nazwisko klienta indywidualnego."),
    )
    nip = models.CharField(
        max_length=20,
        blank=True,
        unique=False,  # NIP może być pusty – nie wymuszamy unikalności dla pustych
        verbose_name=_("NIP"),
        help_text=_("Numer Identyfikacji Podatkowej (opcjonalny)."),
    )
    industry = models.CharField(
        max_length=20,
        choices=Industry,
        default=Industry.INNE,
        verbose_name=_("branża"),
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("adres"),
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("miasto"),
    )
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("kod pocztowy"),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("telefon"),
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("e-mail"),
    )
    website = models.URLField(
        blank=True,
        verbose_name=_("strona www"),
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_companies",
        verbose_name=_("opiekun handlowy"),
        help_text=_("Handlowiec odpowiedzialny za tę firmę."),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("uwagi"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("aktywna"),
        help_text=_("Odznacz aby zarchiwizować firmę bez usuwania danych."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("data dodania"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("data modyfikacji"),
    )

    class Meta:
        verbose_name = _("firma")
        verbose_name_plural = _("firmy")
        ordering = ["name"]

    def __str__(self) -> str:
        """Zwraca nazwę firmy."""
        return self.name

    @property
    def full_address(self) -> str:
        """Zwraca pełny adres jako jeden ciąg znaków.

        Returns:
            Sformatowany adres lub pusty string gdy brak danych.
        """
        parts = [self.address, self.postal_code, self.city]
        return ", ".join(part for part in parts if part)
