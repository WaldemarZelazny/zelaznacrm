"""Modele aplikacji notes – notatki CRM."""

from __future__ import annotations

import logging
from typing import Union

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead

logger = logging.getLogger(__name__)

# Maksymalna dlugosc skroconego podgladu tresci notatki
_SHORT_CONTENT_LIMIT = 100

# Typ zwracany przez related_object
RelatedObject = Union[Deal, Lead, Company, Contact, None]


class Note(models.Model):
    """Notatka tekstowa powiazana z obiektem CRM.

    Krotka notatka handlowca dotyczaca firmy, leada, umowy lub kontaktu.
    Jeden rekord Note moze byc powiazany jednoczesnie z kilkoma obiektami,
    jednak semantycznie priorytet ma: Deal > Lead > Company > Contact.
    Metoda related_object zwraca najwazniejszy powiazany obiekt.

    Uwaga o related_name: Company i Contact maja juz pole TextField `notes`,
    dlatego uzywamy odrozniajacych sie nazw dla odwroconych relacji:
    company_notes, contact_notes (vs notes dla Lead i Deal, ktore nie
    posiadaja pola o tej nazwie).

    Attributes:
        content: Pelna tresc notatki.
        author: Autor notatki (FK -> User, SET_NULL).
        company: Powiazana firma (opcjonalna, FK SET_NULL).
        lead: Powiazany lead (opcjonalny, FK SET_NULL).
        deal: Powiazana umowa (opcjonalna, FK SET_NULL).
        contact: Powiazana osoba kontaktowa (opcjonalna, FK SET_NULL).
        created_at: Data i godzina dodania notatki (automatyczna).
        updated_at: Data ostatniej edycji (automatyczna).
    """

    content = models.TextField(
        verbose_name=_("tresc"),
        help_text=_("Tresc notatki handlowca."),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
        verbose_name=_("autor"),
    )
    # related_name="company_notes" – Company.notes jest juz polem TextField
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="company_notes",
        verbose_name=_("firma"),
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
        verbose_name=_("lead"),
    )
    deal = models.ForeignKey(
        Deal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes",
        verbose_name=_("umowa"),
    )
    # related_name="contact_notes" – Contact.notes jest juz polem TextField
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_notes",
        verbose_name=_("kontakt"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("data dodania"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("data edycji"),
    )

    class Meta:
        verbose_name = _("notatka")
        verbose_name_plural = _("notatki")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Zwraca skrocona tresc i autora notatki."""
        author_name = self.author.get_full_name() if self.author else "—"
        return f"Notatka: {self.short_content} ({author_name})"

    # ------------------------------------------------------------------
    # Wlasciwosci
    # ------------------------------------------------------------------

    @property
    def short_content(self) -> str:
        """Zwraca pierwsze 100 znakow tresci z wielokropkiem jesli dluzsza.

        Returns:
            Skrocona tresc notatki lub pelna tresc gdy nie przekracza limitu.
        """
        if len(self.content) > _SHORT_CONTENT_LIMIT:
            return f"{self.content[:_SHORT_CONTENT_LIMIT]}..."
        return self.content

    @property
    def related_object(self) -> RelatedObject:
        """Zwraca najwazniejszy powiazany obiekt CRM.

        Priorytety: Deal > Lead > Company > Contact.
        Przydatne do wyswietlania kontekstu notatki w interfejsie.

        Returns:
            Pierwszy znaleziony obiekt wg priorytetu lub None jesli
            notatka nie ma zadnego powiazania.
        """
        return self.deal or self.lead or self.company or self.contact
