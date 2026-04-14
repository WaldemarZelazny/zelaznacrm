"""Modele aplikacji reports – logi aktywnosci CRM."""

from __future__ import annotations

import logging
from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class ActivityLog(models.Model):
    """Niemutowalny log aktywnosci uzytkownikow w systemie CRM.

    Kazdy wpis reprezentuje pojedyncze zdarzenie (utworzenie, edycja,
    usuniecie lub wyswietlenie obiektu). Logi sa tylko do odczytu –
    nie posiadaja pola updated_at i sa zabezpieczone w Adminie przed
    edycja i dodawaniem nowych wpisow recznie.

    Nowe wpisy tworzy sie wylacznie przez classmethod ActivityLog.log().

    Attributes:
        user: Uzytkownik wykonujacy akcje (FK -> User, SET_NULL).
        action: Typ akcji (TextChoices: UTWORZONO/ZAKTUALIZOWANO/USUNIETO/WYSWIETLONO).
        model_name: Nazwa klasy modelu (np. "Lead", "Company").
        object_id: ID obiektu, ktorego dotyczy zdarzenie.
        object_repr: Reprezentacja tekstowa obiektu (__str__) w chwili zdarzenia.
        description: Opcjonalny dodatkowy opis zdarzenia.
        ip_address: Adres IP klienta (opcjonalny).
        created_at: Znacznik czasu zdarzenia (auto, niemutowalny).
    """

    class Action(models.TextChoices):
        """Typy akcji rejestrowanych w logu aktywnosci."""

        UTWORZONO = "UTWORZONO", _("Utworzono")
        ZAKTUALIZOWANO = "ZAKTUALIZOWANO", _("Zaktualizowano")
        USUNIETO = "USUNIETO", _("Usunieto")
        WYSWIETLONO = "WYSWIETLONO", _("Wyswietlono")

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
        verbose_name=_("uzytkownik"),
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name=_("akcja"),
    )
    model_name = models.CharField(
        max_length=100,
        verbose_name=_("nazwa modelu"),
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_("ID obiektu"),
    )
    object_repr = models.CharField(
        max_length=200,
        verbose_name=_("reprezentacja obiektu"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("opis"),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("adres IP"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("data zdarzenia"),
    )

    class Meta:
        verbose_name = _("log aktywnosci")
        verbose_name_plural = _("logi aktywnosci")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Zwraca krotki opis zdarzenia: akcja, model i repr obiektu."""
        user_str = self.user.username if self.user else "—"
        return f"[{self.action}] {self.model_name} #{self.object_id} ({user_str})"

    # ------------------------------------------------------------------
    # Metody klasowe
    # ------------------------------------------------------------------

    @classmethod
    def log(
        cls,
        user: Optional[User],
        action: str,
        obj: models.Model,
        description: str = "",
        ip: Optional[str] = None,
    ) -> "ActivityLog":
        """Tworzy nowy wpis w logu aktywnosci.

        Automatycznie wypelnia model_name na podstawie klasy obiektu
        oraz object_repr przez wywolanie str(obj).

        Args:
            user: Uzytkownik wykonujacy akcje lub None gdy systemowy.
            action: Wartosc z ActivityLog.Action (np. ActivityLog.Action.UTWORZONO).
            obj: Obiekt Django ORM, ktorego dotyczy zdarzenie.
            description: Opcjonalny dodatkowy opis.
            ip: Adres IP klienta (opcjonalny).

        Returns:
            Nowo utworzony obiekt ActivityLog.
        """
        entry = cls.objects.create(
            user=user,
            action=action,
            model_name=obj.__class__.__name__,
            object_id=obj.pk,
            object_repr=str(obj)[:200],
            description=description,
            ip_address=ip,
        )
        logger.info(
            "ActivityLog: %s %s #%s przez %s",
            action,
            obj.__class__.__name__,
            obj.pk,
            user.username if user else "system",
        )
        return entry

    # ------------------------------------------------------------------
    # Wlasciwosci
    # ------------------------------------------------------------------

    @property
    def action_icon(self) -> str:
        """Zwraca emoji reprezentujace typ akcji.

        Returns:
            Emoji odpowiadajace akcji: utworzenie, edycja, usuniecie lub wyswietlenie.
        """
        icons = {
            self.Action.UTWORZONO: "✅",
            self.Action.ZAKTUALIZOWANO: "✏️",
            self.Action.USUNIETO: "🗑️",
            self.Action.WYSWIETLONO: "👁️",
        }
        return icons.get(self.action, "❓")
