"""Konfiguracja panelu administracyjnego dla aplikacji companies."""

from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Panel administracyjny firm i klientów."""

    list_display = (
        "name",
        "industry",
        "city",
        "phone",
        "email",
        "owner",
        "is_active",
        "created_at",
    )
    list_filter = ("industry", "is_active", "city")
    search_fields = ("name", "nip", "city", "email", "phone")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
    list_per_page = 25

    fieldsets = (
        (
            _("Dane podstawowe"),
            {
                "fields": ("name", "nip", "industry", "is_active"),
            },
        ),
        (
            _("Dane kontaktowe"),
            {
                "fields": (
                    "address",
                    "city",
                    "postal_code",
                    "phone",
                    "email",
                    "website",
                ),
            },
        ),
        (
            _("Zarządzanie"),
            {
                "fields": ("owner", "notes"),
            },
        ),
        (
            _("Daty"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
