"""Konfiguracja panelu administracyjnego dla aplikacji documents."""

from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Panel administracyjny dokumentow CRM."""

    list_display = (
        "title",
        "doc_type",
        "file_extension_display",
        "file_size_display_col",
        "company",
        "created_by",
        "created_at",
    )
    list_filter = ("doc_type",)
    search_fields = (
        "title",
        "description",
        "company__name",
        "created_by__username",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "file_extension_display",
        "file_size_display_col",
    )
    ordering = ("-created_at",)
    list_select_related = ("company", "lead", "deal", "created_by")
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Dokument"),
            {
                "fields": ("title", "doc_type", "file", "description"),
            },
        ),
        (
            _("Informacje o pliku"),
            {
                "fields": ("file_extension_display", "file_size_display_col"),
            },
        ),
        (
            _("Powiazania"),
            {
                "fields": ("company", "lead", "deal", "created_by"),
                "description": _(
                    "Dokument moze byc powiazany z firma, leadem i/lub umowa."
                ),
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

    @admin.display(description=_("Rozszerzenie"))
    def file_extension_display(self, obj: Document) -> str:
        """Zwraca rozszerzenie pliku lub myslnik gdy brak."""
        return obj.file_extension or "—"

    @admin.display(description=_("Rozmiar"))
    def file_size_display_col(self, obj: Document) -> str:
        """Zwraca czytelny rozmiar pliku."""
        return obj.file_size_display
