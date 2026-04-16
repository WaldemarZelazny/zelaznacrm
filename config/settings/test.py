"""
Ustawienia Django dla srodowiska testowego.

Rozszerza base.py bez debug_toolbar i django_extensions
(te pakiety powoduja bledy podczas testow pytest).
"""

from __future__ import annotations

from .base import *  # noqa: F401, F403
from .base import BASE_DIR  # noqa: F401

# ---------------------------------------------------------------------------
# Tryb debugowania – wylaczony w testach
# ---------------------------------------------------------------------------
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# ---------------------------------------------------------------------------
# Baza danych – SQLite in-memory (najszybsza dla testow)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ---------------------------------------------------------------------------
# Email – wypisuj do konsoli
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# Hasla – prostszy walidator przyspiesza testy
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = []
