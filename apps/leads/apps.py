"""Konfiguracja aplikacji Django: leads."""

from __future__ import annotations

from django.apps import AppConfig


class LeadsConfig(AppConfig):
    """Aplikacja zarządzająca leadami i lejkiem sprzedażowym."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.leads"
    verbose_name = "Leady"
