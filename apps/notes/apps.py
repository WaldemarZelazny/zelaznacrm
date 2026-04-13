"""Konfiguracja aplikacji Django: notes."""

from __future__ import annotations

from django.apps import AppConfig


class NotesConfig(AppConfig):
    """Aplikacja zarządzająca notatkami."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notes"
    verbose_name = "Notatki"
