"""Konfiguracja panelu administracyjnego dla aplikacji contacts."""

from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Panel administracyjny osób kontaktowych."""

    list_display = (
        "full_name",
        "company",
        "position",
        "department",
        "email",
        "phone",
        "owner",
        "is_active",
    )
    list_filter = ("department", "is_active", "company")
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "mobile",
        "position",
        "company__name",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("last_name", "first_name")
    list_select_related = ("company", "owner")
    list_per_page = 25

    fieldsets = (
        (
            _("Dane osobowe"),
            {
                "fields": ("first_name", "last_name", "position", "department"),
            },
        ),
        (
            _("Firma"),
            {
                "fields": ("company", "owner"),
            },
        ),
        (
            _("Dane kontaktowe"),
            {
                "fields": ("email", "phone", "mobile"),
            },
        ),
        (
            _("Dodatkowe"),
            {
                "fields": ("notes", "is_active"),
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

    @admin.display(description=_("Imię i nazwisko"), ordering="last_name")
    def full_name(self, obj: Contact) -> str:
        """Zwraca pełne imię i nazwisko kontaktu."""
        return obj.full_name
