"""Konfiguracja aplikacji Django: tasks."""

from __future__ import annotations

from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Aplikacja zarządzająca zadaniami i kalendarzem."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tasks"
    verbose_name = "Zadania"
