"""Konfiguracja aplikacji Django: reports."""

from __future__ import annotations

from django.apps import AppConfig


class ReportsConfig(AppConfig):
    """Aplikacja zarządzająca raportami i logami aktywności."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    verbose_name = "Raporty"
