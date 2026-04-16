"""Konfiguracja aplikacji Django: contacts."""

from __future__ import annotations

from django.apps import AppConfig


class ContactsConfig(AppConfig):
    """Aplikacja zarządzająca osobami kontaktowymi."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contacts"
    verbose_name = "Kontakty"
