"""
Ustawienia Django dla środowiska produkcyjnego.

Nadpisuje bazowe ustawienia z base.py:
- DEBUG = False
- Baza danych: PostgreSQL
- Pełne ustawienia bezpieczeństwa (HTTPS, secure cookies)
- WhiteNoise do serwowania plików statycznych
"""

from __future__ import annotations

from .base import *  # noqa: F401, F403
from .base import MIDDLEWARE, env

# ---------------------------------------------------------------------------
# Tryb produkcyjny
# ---------------------------------------------------------------------------
DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")


# ---------------------------------------------------------------------------
# Baza danych – PostgreSQL
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL")
}


# ---------------------------------------------------------------------------
# Bezpieczeństwo – wymagane przy HTTPS
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000        # 1 rok
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True


# ---------------------------------------------------------------------------
# WhiteNoise – serwowanie plików statycznych bez dodatkowego serwera
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}


# ---------------------------------------------------------------------------
# Email – konfiguracja SMTP (wypełnij w .env)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@zelaznaCRM.pl")
