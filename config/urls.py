"""
Główna konfiguracja URL dla projektu ZelaznaCRM.

Routing per-aplikacja jest zdefiniowany w apps/<app>/urls.py
i dołączany przez include() z odpowiednim namespace.
"""

from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Panel administracyjny Django
    path("admin/", admin.site.urls),
    # Strona główna (landing page) + logowanie
    path("", include("apps.accounts.urls", namespace="accounts")),
    # Moduły CRM
    path("companies/", include("apps.companies.urls", namespace="companies")),
    path("contacts/", include("apps.contacts.urls", namespace="contacts")),
    path("leads/", include("apps.leads.urls", namespace="leads")),
    path("deals/", include("apps.deals.urls", namespace="deals")),
    path("tasks/", include("apps.tasks.urls", namespace="tasks")),
    path("documents/", include("apps.documents.urls", namespace="documents")),
    path("notes/", include("apps.notes.urls", namespace="notes")),
    path("reports/", include("apps.reports.urls", namespace="reports")),
]

# W trybie deweloperskim serwuj pliki media przez Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # django-debug-toolbar
    import debug_toolbar  # noqa: E402

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
