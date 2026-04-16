"""Konfiguracja panelu administracyjnego dla aplikacji deals."""

from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Deal


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    """Panel administracyjny umów handlowych."""

    list_display = (
        "title",
        "company",
        "owner",
        "status",
        "value_display",
        "close_date",
        "signed_at",
        "is_overdue",
    )
    list_filter = ("status", "owner", "signed_at")
    search_fields = ("title", "company__name", "owner__username", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    list_select_related = ("company", "lead", "owner")
    list_per_page = 25
    date_hierarchy = "close_date"

    fieldsets = (
        (
            _("Dane umowy"),
            {
                "fields": ("title", "company", "lead", "description"),
            },
        ),
        (
            _("Status i wartość"),
            {
                "fields": ("status", "value", "signed_at", "close_date"),
            },
        ),
        (
            _("Przypisanie"),
            {
                "fields": ("owner",),
            },
        ),
        (
            _("Daty systemowe"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Wartość"), ordering="value")
    def value_display(self, obj: Deal) -> str:
        """Zwraca wartość umowy sformatowaną jako PLN."""
        return obj.value_display

    @admin.display(description=_("Po terminie"), boolean=True)
    def is_overdue(self, obj: Deal) -> bool:
        """Zwraca True gdy aktywna umowa przekroczyła termin."""
        return obj.is_overdue
