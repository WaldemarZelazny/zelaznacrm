"""Modele aplikacji leads – lejek sprzedażowy systemu ZelaznaCRM."""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.contacts.models import Contact

logger = logging.getLogger(__name__)


class WorkflowStage(models.Model):
    """Etap lejka sprzedażowego (kolumna Kanban).

    Definiuje kolejność i wygląd kolumn w widoku Kanban. Etapy
    tworzone są przez migrację danych – zestaw domyślny: Nowy, Kontakt,
    Oferta, Negocjacje, Wygrana, Przegrana.

    Attributes:
        name: Wyświetlana nazwa etapu (np. „Oferta").
        order: Kolejność wyświetlania na tablicy Kanban (niższy = pierwszy).
        color: Kolor hex kolumny Kanban (np. „#28a745").
        is_active: Czy etap jest widoczny na tablicy.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("nazwa etapu"),
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("kolejność"),
        help_text=_("Niższy numer = wcześniej na tablicy Kanban."),
    )
    color = models.CharField(
        max_length=7,
        default="#6c757d",
        verbose_name=_("kolor"),
        help_text=_("Kolor hex kolumny Kanban, np. #28a745."),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("aktywny"),
    )

    class Meta:
        verbose_name = _("etap lejka")
        verbose_name_plural = _("etapy lejka")
        ordering = ["order"]

    def __str__(self) -> str:
        """Zwraca nazwę etapu z numerem kolejności."""
        return f"{self.order}. {self.name}"


class Lead(models.Model):
    """Lead sprzedażowy – szansa sprzedaży w toku.

    Centralny model lejka sprzedażowego. Reprezentuje potencjalną
    transakcję od pierwszego kontaktu aż do wygrania lub przegranej.
    Powiązany z firmą, opcjonalnie z konkretną osobą kontaktową,
    i przypisany do etapu Kanban (WorkflowStage).

    Attributes:
        title: Krótki tytuł leada (temat / okazja).
        company: Firma, której dotyczy lead (FK → Company).
        contact: Osoba kontaktowa w firmie (opcjonalna, FK → Contact).
        owner: Odpowiedzialny handlowiec (FK → User, SET_NULL).
        status: Aktualny status leada (TextChoices).
        source: Źródło pozyskania leada (TextChoices).
        value: Szacowana wartość transakcji w PLN.
        stage: Aktualny etap na tablicy Kanban (FK → WorkflowStage).
        description: Opis / notatka do leada.
        created_at: Data utworzenia (automatyczna).
        updated_at: Data ostatniej modyfikacji (automatyczna).
        closed_at: Data zamknięcia leada (None = lead otwarty).
    """

    class Status(models.TextChoices):
        """Status leada w lejku sprzedażowym."""

        NOWY = "NOWY", _("Nowy")
        W_TOKU = "W_TOKU", _("W toku")
        WYGRANA = "WYGRANA", _("Wygrana")
        PRZEGRANA = "PRZEGRANA", _("Przegrana")
        ANULOWANY = "ANULOWANY", _("Anulowany")

    class Source(models.TextChoices):
        """Źródło pozyskania leada."""

        FORMULARZ = "FORMULARZ", _("Formularz www")
        POLECENIE = "POLECENIE", _("Polecenie")
        COLD_CALL = "COLD_CALL", _("Cold call")
        KAMPANIA = "KAMPANIA", _("Kampania marketingowa")
        TARGI = "TARGI", _("Targi / Wydarzenie")
        INNE = "INNE", _("Inne")

    title = models.CharField(
        max_length=200,
        verbose_name=_("tytuł"),
        help_text=_("Krótki opis okazji sprzedażowej."),
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="leads",
        verbose_name=_("firma"),
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
        verbose_name=_("kontakt"),
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_leads",
        verbose_name=_("handlowiec"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.NOWY,
        verbose_name=_("status"),
    )
    source = models.CharField(
        max_length=20,
        choices=Source,
        default=Source.INNE,
        verbose_name=_("źródło"),
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("wartość (PLN)"),
        help_text=_("Szacowana wartość transakcji w złotych."),
    )
    stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.PROTECT,
        related_name="leads",
        verbose_name=_("etap"),
        help_text=_("Aktualny etap na tablicy Kanban."),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("opis"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("data utworzenia"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("data modyfikacji"),
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("data zamknięcia"),
        help_text=_("Ustawiana automatycznie przy wygranej lub przegranej."),
    )

    class Meta:
        verbose_name = _("lead")
        verbose_name_plural = _("leady")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Zwraca tytuł leada i nazwę firmy."""
        return f"{self.title} – {self.company.name}"

    @property
    def is_closed(self) -> bool:
        """Sprawdza czy lead jest zamknięty (wygrana, przegrana lub anulowany)."""
        return self.status in (
            self.Status.WYGRANA,
            self.Status.PRZEGRANA,
            self.Status.ANULOWANY,
        )

    def close(self, status: str) -> None:
        """Zamyka lead z podanym statusem końcowym.

        Ustawia status, zapisuje datę i godzinę zamknięcia (closed_at = now).
        Wywołanie na już zamkniętym leadzie aktualizuje closed_at.

        Args:
            status: Wartość z Lead.Status – dozwolone: WYGRANA, PRZEGRANA,
                    ANULOWANY.

        Raises:
            ValueError: Gdy podany status nie jest statusem zamykającym.
        """
        closing_statuses = (
            self.Status.WYGRANA,
            self.Status.PRZEGRANA,
            self.Status.ANULOWANY,
        )
        if status not in closing_statuses:
            raise ValueError(
                f"Status '{status}' nie jest statusem zamykającym. "
                f"Dozwolone: {', '.join(closing_statuses)}."
            )
        self.status = status
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])
        logger.info(
            "Lead #%s '%s' zamknięty ze statusem %s.", self.pk, self.title, status
        )

    @property
    def value_display(self) -> str:
        """Zwraca wartość leada sformatowaną jako PLN."""
        return f"{self.value:,.2f} PLN".replace(",", " ")
