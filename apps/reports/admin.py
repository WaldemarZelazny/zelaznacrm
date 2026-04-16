"""Konfiguracja panelu administracyjnego dla aplikacji reports."""

from __future__ import annotations

from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Panel administracyjny logow aktywnosci – tylko do odczytu.

    Logi sa niemutowalne: nie mozna ich recznie tworzyc ani edytowac
    z poziomu Admina. Dostepne jest tylko przegladanie i filtrowanie.
    """

    list_display = (
        "created_at",
        "user",
        "action",
        "model_name",
        "object_id",
        "object_repr",
        "ip_address",
    )
    list_filter = ("action", "model_name", "user")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "model_name",
        "object_repr",
        "description",
    )
    readonly_fields = (
        "user",
        "action",
        "model_name",
        "object_id",
        "object_repr",
        "description",
        "ip_address",
        "created_at",
    )
    ordering = ("-created_at",)
    list_select_related = ("user",)
    list_per_page = 50
    date_hierarchy = "created_at"

    def has_add_permission(self, request) -> bool:
        """Blokuje reczne tworzenie logow z poziomu Admina."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Blokuje edycje logow – sa niemutowalne."""
        return False
