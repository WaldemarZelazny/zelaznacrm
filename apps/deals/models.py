"""Modele aplikacji deals – umowy i transakcje systemu ZelaznaCRM."""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.leads.models import Lead

logger = logging.getLogger(__name__)


class Deal(models.Model):
    """Umowa lub transakcja handlowa.

    Reprezentuje finalne porozumienie z klientem – może powstać bezpośrednio
    lub jako wynik zamkniętego leada. Śledzony jest termin realizacji
    (close_date) oraz data podpisania (signed_at).

    Attributes:
        title: Tytuł umowy (np. „Dostawa serwerów Q3 2026").
        company: Firma-strona umowy (FK → Company, CASCADE).
        lead: Lead źródłowy (FK → Lead, SET_NULL; opcjonalny).
        owner: Odpowiedzialny handlowiec (FK → User, SET_NULL).
        status: Aktualny status umowy (TextChoices).
        value: Wartość umowy w PLN.
        signed_at: Data podpisania umowy (None = niepodpisana).
        close_date: Planowana data realizacji / zamknięcia.
        description: Opis warunków lub dodatkowe uwagi.
        created_at: Data utworzenia rekordu (automatyczna).
        updated_at: Data ostatniej modyfikacji (automatyczna).
    """

    class Status(models.TextChoices):
        """Status umowy handlowej."""

        AKTYWNA = "AKTYWNA", _("Aktywna")
        ZREALIZOWANA = "ZREALIZOWANA", _("Zrealizowana")
        ANULOWANA = "ANULOWANA", _("Anulowana")

    title = models.CharField(
        max_length=200,
        verbose_name=_("tytuł umowy"),
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="deals",
        verbose_name=_("firma"),
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
        verbose_name=_("lead źródłowy"),
        help_text=_("Lead, z którego powstała ta umowa (opcjonalny)."),
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_deals",
        verbose_name=_("handlowiec"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.AKTYWNA,
        verbose_name=_("status"),
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("wartość (PLN)"),
        help_text=_("Wartość umowy w złotych brutto."),
    )
    signed_at = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("data podpisania"),
        help_text=_("Ustawiana automatycznie przy zatwierdzeniu umowy."),
    )
    close_date = models.DateField(
        verbose_name=_("termin realizacji"),
        help_text=_("Planowana data zamknięcia lub dostarczenia."),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("opis / warunki"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("data utworzenia"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("data modyfikacji"),
    )

    class Meta:
        verbose_name = _("umowa")
        verbose_name_plural = _("umowy")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="deal_status_idx"),
        ]

    def __str__(self) -> str:
        """Zwraca tytuł umowy i nazwę firmy."""
        return f"{self.title} – {self.company.name}"

    # ------------------------------------------------------------------
    # Właściwości
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """Sprawdza czy umowa ma status AKTYWNA."""
        return self.status == self.Status.AKTYWNA

    @property
    def is_overdue(self) -> bool:
        """Sprawdza czy aktywna umowa przekroczyła termin realizacji.

        Returns:
            True gdy status == AKTYWNA i close_date < dzisiaj.
            False dla umów zakończonych lub bez przekroczonego terminu.
        """
        if not self.is_active:
            return False
        return self.close_date < timezone.localdate()

    @property
    def value_display(self) -> str:
        """Zwraca wartość umowy sformatowaną jako PLN."""
        return f"{self.value:,.2f} PLN".replace(",", " ")

    # ------------------------------------------------------------------
    # Metody biznesowe
    # ------------------------------------------------------------------

    def complete(self) -> None:
        """Zatwierdza umowę jako zrealizowaną.

        Ustawia status ZREALIZOWANA i zapisuje dzisiejszą datę jako
        signed_at, jeśli nie była jeszcze ustawiona. Wywołanie na
        umowie już zrealizowanej jest idempotentne.

        Raises:
            ValueError: Gdy umowa ma status ANULOWANA.
        """
        if self.status == self.Status.ANULOWANA:
            raise ValueError(f"Nie można zrealizować anulowanej umowy (pk={self.pk}).")
        self.status = self.Status.ZREALIZOWANA
        if not self.signed_at:
            self.signed_at = timezone.localdate()
        self.save(update_fields=["status", "signed_at", "updated_at"])
        logger.info("Umowa #%s '%s' oznaczona jako zrealizowana.", self.pk, self.title)

    def cancel(self) -> None:
        """Anuluje umowę.

        Ustawia status ANULOWANA. Wywołanie na już anulowanej umowie
        jest idempotentne.

        Raises:
            ValueError: Gdy umowa ma status ZREALIZOWANA.
        """
        if self.status == self.Status.ZREALIZOWANA:
            raise ValueError(f"Nie można anulować zrealizowanej umowy (pk={self.pk}).")
        self.status = self.Status.ANULOWANA
        self.save(update_fields=["status", "updated_at"])
        logger.info("Umowa #%s '%s' anulowana.", self.pk, self.title)
