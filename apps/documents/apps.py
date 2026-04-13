"""Konfiguracja aplikacji Django: documents."""

from __future__ import annotations

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Aplikacja zarządzająca dokumentami i generowaniem PDF."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"
    verbose_name = "Dokumenty"
