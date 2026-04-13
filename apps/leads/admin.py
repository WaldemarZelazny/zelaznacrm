"""Konfiguracja panelu administracyjnego dla aplikacji leads."""

from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Lead, WorkflowStage


@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    """Panel administracyjny etapów lejka sprzedażowego."""

    list_display = ("name", "order", "color", "is_active")
    list_display_links = ("name",)
    list_editable = ("order", "color", "is_active")
    ordering = ("order",)
    search_fields = ("name",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Panel administracyjny leadów sprzedażowych."""

    list_display = (
        "title",
        "company",
        "contact",
        "owner",
        "status",
        "stage",
        "value_display",
        "created_at",
        "is_closed",
    )
    list_filter = ("status", "source", "stage", "owner")
    search_fields = ("title", "company__name", "contact__last_name", "owner__username")
    readonly_fields = ("created_at", "updated_at", "closed_at")
    ordering = ("-created_at",)
    list_select_related = ("company", "contact", "owner", "stage")
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Dane leada"),
            {
                "fields": ("title", "company", "contact", "description"),
            },
        ),
        (
            _("Lejek sprzedażowy"),
            {
                "fields": ("status", "stage", "source", "value"),
            },
        ),
        (
            _("Przypisanie"),
            {
                "fields": ("owner",),
            },
        ),
        (
            _("Daty"),
            {
                "fields": ("created_at", "updated_at", "closed_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description=_("Wartość"), ordering="value")
    def value_display(self, obj: Lead) -> str:
        """Zwraca wartość leada w formacie PLN."""
        return obj.value_display

    @admin.display(description=_("Zamknięty"), boolean=True)
    def is_closed(self, obj: Lead) -> bool:
        """Pokazuje czy lead jest zamknięty."""
        return obj.is_closed
