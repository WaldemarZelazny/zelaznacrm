"""Modele aplikacji contacts – osoby kontaktowe w firmach CRM."""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company

logger = logging.getLogger(__name__)


class Contact(models.Model):
    """Osoba kontaktowa powiązana z firmą w systemie CRM.

    Reprezentuje konkretną osobę (np. decydenta, pracownika) w firmie-kliencie.
    Jeden kontakt należy do jednej firmy; jeden handlowiec może mieć wielu
    kontaktów. Usunięcie firmy kasuje wszystkie jej kontakty (CASCADE).

    Attributes:
        first_name: Imię osoby kontaktowej.
        last_name: Nazwisko osoby kontaktowej.
        company: Firma, w której pracuje kontakt (FK → Company).
        position: Stanowisko lub tytuł służbowy.
        department: Dział / departament (opcjonalny).
        email: Służbowy adres e-mail.
        phone: Numer telefonu służbowego.
        mobile: Numer telefonu komórkowego (opcjonalny).
        owner: Opiekun handlowy – handlowiec odpowiedzialny za kontakt.
        notes: Dodatkowe uwagi o osobie.
        is_active: Czy kontakt jest aktywny.
        created_at: Data dodania kontaktu (automatyczna).
        updated_at: Data ostatniej modyfikacji (automatyczna).
    """

    class Department(models.TextChoices):
        """Dział / departament osoby kontaktowej."""

        ZARZAD = "ZARZAD", _("Zarząd")
        SPRZEDAZ = "SPRZEDAZ", _("Sprzedaż")
        ZAKUPY = "ZAKUPY", _("Zakupy")
        IT = "IT", _("IT")
        FINANSE = "FINANSE", _("Finanse / Księgowość")
        HR = "HR", _("HR / Kadry")
        MARKETING = "MARKETING", _("Marketing")
        PRODUKCJA = "PRODUKCJA", _("Produkcja")
        LOGISTYKA = "LOGISTYKA", _("Logistyka")
        INNE = "INNE", _("Inne")

    first_name = models.CharField(
        max_length=100,
        verbose_name=_("imię"),
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_("nazwisko"),
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name=_("firma"),
        help_text=_("Firma, w której pracuje ta osoba."),
    )
    position = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("stanowisko"),
    )
    department = models.CharField(
        max_length=20,
        choices=Department,
        default=Department.INNE,
        verbose_name=_("dział"),
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("e-mail"),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("telefon"),
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("telefon komórkowy"),
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_contacts",
        verbose_name=_("opiekun handlowy"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("uwagi"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("aktywny"),
        help_text=_("Odznacz aby zarchiwizować kontakt bez usuwania."),
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
        verbose_name = _("kontakt")
        verbose_name_plural = _("kontakty")
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        """Zwraca pełne imię i nazwisko oraz nazwę firmy."""
        return f"{self.first_name} {self.last_name} ({self.company.name})"

    @property
    def full_name(self) -> str:
        """Zwraca pełne imię i nazwisko kontaktu."""
        return f"{self.first_name} {self.last_name}"

    @property
    def primary_phone(self) -> str:
        """Zwraca pierwszy dostępny numer telefonu: telefon lub komórkowy.

        Returns:
            Numer telefonu (służbowy lub komórkowy) albo pusty string.
        """
        return self.phone or self.mobile
