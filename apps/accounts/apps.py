"""Konfiguracja aplikacji Django: accounts."""

from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Aplikacja zarządzająca użytkownikami i rolami (ADMIN, HANDLOWIEC)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Konta i użytkownicy"

    def ready(self) -> None:
        """Rejestruje sygnały aplikacji accounts po załadowaniu Django."""
        import apps.accounts.signals  # noqa: F401
