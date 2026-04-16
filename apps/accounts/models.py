"""Modele aplikacji accounts – użytkownicy i role systemu ZelaznaCRM."""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """Profil użytkownika rozszerzający wbudowany model User Django.

    Przechowuje rolę (ADMIN / HANDLOWIEC), numer telefonu i opcjonalny awatar.
    Relacja OneToOne gwarantuje jeden profil na konto.

    Attributes:
        user: Powiązany obiekt User (Django auth).
        role: Rola w systemie – ADMIN lub HANDLOWIEC.
        phone: Numer telefonu kontaktowego.
        avatar: Opcjonalne zdjęcie profilowe.
        created_at: Data i godzina założenia profilu (automatyczna).
    """

    class Role(models.TextChoices):
        """Role użytkowników w systemie CRM."""

        ADMIN = "ADMIN", _("Administrator")
        HANDLOWIEC = "HANDLOWIEC", _("Handlowiec")

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("użytkownik"),
    )
    role = models.CharField(
        max_length=20,
        choices=Role,
        default=Role.HANDLOWIEC,
        verbose_name=_("rola"),
        help_text=_("Rola określa poziom dostępu w systemie."),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("telefon"),
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name=_("awatar"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("data utworzenia"),
    )

    class Meta:
        verbose_name = _("profil użytkownika")
        verbose_name_plural = _("profile użytkowników")
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self) -> str:
        """Zwraca czytelną reprezentację profilu: imię, nazwisko i rola."""
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} ({self.get_role_display()})"

    @property
    def is_admin(self) -> bool:
        """Sprawdza czy użytkownik posiada rolę administratora."""
        return self.role == self.Role.ADMIN

    @property
    def full_name(self) -> str:
        """Zwraca pełne imię i nazwisko lub nazwę użytkownika."""
        return self.user.get_full_name() or self.user.username
