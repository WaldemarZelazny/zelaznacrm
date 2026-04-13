"""
Ustawienia Django dla środowiska deweloperskiego.

Nadpisuje bazowe ustawienia z base.py:
- DEBUG = True
- Baza danych: SQLite (szybka konfiguracja lokalna)
- django-debug-toolbar włączony
- django-extensions dostępny
"""

from __future__ import annotations

from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

# ---------------------------------------------------------------------------
# Tryb debugowania
# ---------------------------------------------------------------------------
DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])


# ---------------------------------------------------------------------------
# Baza danych – SQLite (lokalne testy)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}


# ---------------------------------------------------------------------------
# Narzędzia deweloperskie
# ---------------------------------------------------------------------------
INSTALLED_APPS = INSTALLED_APPS + [
    "debug_toolbar",
    "django_extensions",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE

# django-debug-toolbar – tylko dla lokalnych IP
INTERNAL_IPS = ["127.0.0.1"]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}


# ---------------------------------------------------------------------------
# Email – w trybie dev wypisuj do konsoli
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
