"""Konfiguracja panelu administracyjnego dla aplikacji notes."""

from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Note


class RelationFilter(admin.SimpleListFilter):
    """Filtr notatek wedlug rodzaju powiazanego obiektu CRM."""

    title = _("powiazanie")
    parameter_name = "relation"

    def lookups(self, request, model_admin):
        """Opcje filtra: typy obiektow lub brak powiazania."""
        return [
            ("deal", _("Umowa")),
            ("lead", _("Lead")),
            ("company", _("Firma")),
            ("contact", _("Kontakt")),
            ("none", _("Brak powiazania")),
        ]

    def queryset(self, request, queryset):
        """Filtruje queryset wedlug wybranego powiazania."""
        match self.value():
            case "deal":
                return queryset.filter(deal__isnull=False)
            case "lead":
                return queryset.filter(lead__isnull=False)
            case "company":
                return queryset.filter(company__isnull=False)
            case "contact":
                return queryset.filter(contact__isnull=False)
            case "none":
                return queryset.filter(
                    deal__isnull=True,
                    lead__isnull=True,
                    company__isnull=True,
                    contact__isnull=True,
                )
            case _:
                return queryset


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Panel administracyjny notatek CRM."""

    list_display = (
        "short_content_display",
        "author",
        "deal",
        "lead",
        "company",
        "contact",
        "created_at",
    )
    list_filter = (RelationFilter, "author")
    search_fields = (
        "content",
        "author__username",
        "author__first_name",
        "author__last_name",
        "company__name",
        "lead__title",
        "deal__title",
        "contact__last_name",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    list_select_related = ("author", "company", "lead", "deal", "contact")
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Tresc"),
            {
                "fields": ("content", "author"),
            },
        ),
        (
            _("Powiazania"),
            {
                "fields": ("deal", "lead", "company", "contact"),
                "description": _(
                    "Notatka moze byc powiazana z firma, leadem, umowa i/lub kontaktem."
                ),
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

    @admin.display(description=_("Tresc (skrot)"), ordering="content")
    def short_content_display(self, obj: Note) -> str:
        """Zwraca skrocona tresc notatki."""
        return obj.short_content
