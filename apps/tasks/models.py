"""Modele aplikacji tasks – zadania i kalendarz systemu ZelaznaCRM."""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead

logger = logging.getLogger(__name__)


class Task(models.Model):
    """Zadanie CRM powiazane z firma, leadem lub umowa.

    Ujednolicony model aktywnosci handlowca: rozmowa telefoniczna,
    e-mail, spotkanie lub dowolne zadanie. Moze byc powiazane z firma,
    leadem i/lub umowa jednoczesnie. Termin (due_date) sluzy do
    wyswietlania w kalendarzu.

    Attributes:
        title: Krotki tytul zadania.
        description: Opcjonalny szczegolowy opis.
        task_type: Typ aktywnosci (TextChoices).
        priority: Priorytet zadania (TextChoices).
        status: Aktualny status zadania (TextChoices).
        due_date: Termin wykonania (data i godzina).
        completed_at: Moment wykonania zadania (None gdy otwarte).
        assigned_to: Uzytkownik odpowiedzialny za realizacje.
        created_by: Uzytkownik ktory utworzyl zadanie.
        company: Powiazana firma (opcjonalna, FK SET_NULL).
        lead: Powiazany lead (opcjonalny, FK SET_NULL).
        deal: Powiazana umowa (opcjonalna, FK SET_NULL).
        created_at: Data utworzenia (automatyczna).
        updated_at: Data ostatniej modyfikacji (automatyczna).
    """

    class TaskType(models.TextChoices):
        """Typ zadania / aktywnosci CRM."""

        TELEFON = "TELEFON", _("Telefon")
        EMAIL = "EMAIL", _("E-mail")
        SPOTKANIE = "SPOTKANIE", _("Spotkanie")
        ZADANIE = "ZADANIE", _("Zadanie")
        INNE = "INNE", _("Inne")

    class Priority(models.TextChoices):
        """Priorytet zadania – wplyw na sortowanie i widocznosc."""

        NISKI = "NISKI", _("Niski")
        SREDNI = "SREDNI", _("Sredni")
        WYSOKI = "WYSOKI", _("Wysoki")
        PILNY = "PILNY", _("Pilny")

    class Status(models.TextChoices):
        """Status realizacji zadania."""

        DO_ZROBIENIA = "DO_ZROBIENIA", _("Do zrobienia")
        W_TOKU = "W_TOKU", _("W toku")
        WYKONANE = "WYKONANE", _("Wykonane")
        ANULOWANE = "ANULOWANE", _("Anulowane")

    title = models.CharField(
        max_length=200,
        verbose_name=_("tytul"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("opis"),
    )
    task_type = models.CharField(
        max_length=20,
        choices=TaskType,
        default=TaskType.ZADANIE,
        verbose_name=_("typ"),
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority,
        default=Priority.SREDNI,
        verbose_name=_("priorytet"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.DO_ZROBIENIA,
        verbose_name=_("status"),
    )
    due_date = models.DateTimeField(
        verbose_name=_("termin wykonania"),
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("data wykonania"),
        help_text=_("Ustawiana automatycznie przy oznaczeniu jako wykonane."),
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name=_("przypisane do"),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
        verbose_name=_("utworzone przez"),
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name=_("firma"),
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name=_("lead"),
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name=_("umowa"),
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
        verbose_name = _("zadanie")
        verbose_name_plural = _("zadania")
        ordering = ["due_date", "-priority"]

    def __str__(self) -> str:
        """Zwraca tytul zadania z typem i terminem."""
        due = self.due_date.strftime("%d.%m.%Y %H:%M")
        return f"[{self.get_task_type_display()}] {self.title} ({due})"

    # ------------------------------------------------------------------
    # Wlasciwosci
    # ------------------------------------------------------------------

    @property
    def is_done(self) -> bool:
        """Sprawdza czy zadanie zostalo wykonane."""
        return self.status == self.Status.WYKONANE

    @property
    def is_overdue(self) -> bool:
        """Sprawdza czy zadanie jest przeterminowane.

        Zadanie jest przeterminowane gdy termin (due_date) minal,
        a status nie jest WYKONANE ani ANULOWANE.

        Returns:
            True gdy zadanie otwarte i po terminie, False w pozostalych
            przypadkach.
        """
        if self.status in (self.Status.WYKONANE, self.Status.ANULOWANE):
            return False
        return self.due_date < timezone.now()

    # ------------------------------------------------------------------
    # Metody biznesowe
    # ------------------------------------------------------------------

    def complete(self) -> None:
        """Oznacza zadanie jako wykonane i zapisuje czas wykonania.

        Ustawia status WYKONANE i completed_at = now(). Wywolanie na
        juz wykonanym zadaniu jest idempotentne (nie nadpisuje
        completed_at).

        Raises:
            ValueError: Gdy zadanie ma status ANULOWANE.
        """
        if self.status == self.Status.ANULOWANE:
            raise ValueError(f"Nie mozna wykonac anulowanego zadania (pk={self.pk}).")
        self.status = self.Status.WYKONANE
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])
        logger.info("Zadanie #%s '%s' oznaczone jako wykonane.", self.pk, self.title)

    def cancel(self) -> None:
        """Anuluje zadanie.

        Ustawia status ANULOWANE. Wywolanie na juz anulowanym zadaniu
        jest idempotentne.

        Raises:
            ValueError: Gdy zadanie ma status WYKONANE.
        """
        if self.status == self.Status.WYKONANE:
            raise ValueError(f"Nie mozna anulowac wykonanego zadania (pk={self.pk}).")
        self.status = self.Status.ANULOWANE
        self.save(update_fields=["status", "updated_at"])
        logger.info("Zadanie #%s '%s' anulowane.", self.pk, self.title)
