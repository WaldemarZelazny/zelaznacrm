"""Konfiguracja panelu administracyjnego dla aplikacji tasks."""

from __future__ import annotations

from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Task


class OverdueFilter(admin.SimpleListFilter):
    """Filtr zadania przeterminowanych w panelu administracyjnym."""

    title = _("termin")
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        """Zwraca opcje filtra."""
        return [
            ("yes", _("Przeterminowane")),
            ("no", _("W terminie")),
        ]

    def queryset(self, request, queryset):
        """Filtruje queryset wedlug stanu przeterminowania."""
        now = timezone.now()
        open_statuses = (Task.Status.DO_ZROBIENIA, Task.Status.W_TOKU)
        if self.value() == "yes":
            return queryset.filter(status__in=open_statuses, due_date__lt=now)
        if self.value() == "no":
            return queryset.exclude(status__in=open_statuses, due_date__lt=now)
        return queryset


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Panel administracyjny zadan CRM."""

    list_display = (
        "title",
        "task_type",
        "priority",
        "status",
        "assigned_to",
        "due_date",
        "company",
        "is_done",
        "is_overdue",
    )
    list_filter = ("status", "task_type", "priority", OverdueFilter)
    search_fields = (
        "title",
        "description",
        "assigned_to__username",
        "created_by__username",
        "company__name",
    )
    readonly_fields = ("created_at", "updated_at", "completed_at")
    ordering = ("due_date", "-priority")
    list_select_related = ("assigned_to", "created_by", "company", "lead", "deal")
    list_per_page = 25
    date_hierarchy = "due_date"

    fieldsets = (
        (
            _("Zadanie"),
            {
                "fields": ("title", "description", "task_type", "priority", "status"),
            },
        ),
        (
            _("Termin"),
            {
                "fields": ("due_date", "completed_at"),
            },
        ),
        (
            _("Przypisanie"),
            {
                "fields": ("assigned_to", "created_by"),
            },
        ),
        (
            _("Powiazania"),
            {
                "fields": ("company", "lead", "deal"),
                "description": _(
                    "Zadanie moze byc powiazane z firma, leadem i/lub umowa."
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

    @admin.display(description=_("Wykonane"), boolean=True)
    def is_done(self, obj: Task) -> bool:
        """Ikona: czy zadanie wykonane."""
        return obj.is_done

    @admin.display(description=_("Po terminie"), boolean=True)
    def is_overdue(self, obj: Task) -> bool:
        """Ikona: czy zadanie przeterminowane."""
        return obj.is_overdue
