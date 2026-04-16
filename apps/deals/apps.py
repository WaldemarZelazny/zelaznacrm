"""Konfiguracja aplikacji Django: deals."""

from __future__ import annotations

from django.apps import AppConfig


class DealsConfig(AppConfig):
    """Aplikacja zarządzająca umowami i transakcjami."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.deals"
    verbose_name = "Umowy"
