"""Konfiguracja aplikacji Django: companies."""

from __future__ import annotations

from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    """Aplikacja zarządzająca firmami i klientami CRM."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.companies"
    verbose_name = "Firmy"
