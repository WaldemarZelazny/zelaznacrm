"""Widoki dashboardu – strona główna po zalogowaniu."""

from __future__ import annotations

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead
from apps.tasks.models import Task

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Główny panel (dashboard) – podsumowanie systemu CRM.

    Wyświetla liczniki kluczowych modułów oraz zadania wymagające
    uwagi (przeterminowane i na dziś).
    """

    template_name = "dashboard/index.html"
    login_url = "accounts:login"

    def get_context_data(self, **kwargs):
        """Buduje kontekst dashboardu: statystyki i zadania do uwagi."""
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        # Statystyki kluczowych modułów
        ctx["stats"] = {
            "companies": Company.objects.filter(is_active=True).count(),
            "contacts": Contact.objects.filter(is_active=True).count(),
            "leads_open": Lead.objects.exclude(
                status__in=["WYGRANA", "PRZEGRANA", "ANULOWANY"]
            ).count(),
            "deals_active": Deal.objects.filter(status="AKTYWNA").count(),
        }

        # Zadania przeterminowane i na dziś – max 10 pozycji
        ctx["urgent_tasks"] = (
            Task.objects.filter(
                assigned_to=self.request.user,
                status__in=["DO_ZROBIENIA", "W_TOKU"],
                due_date__lte=today,
            )
            .select_related("lead", "deal", "company")
            .order_by("due_date")[:10]
        )

        logger.debug(
            "Dashboard załadowany dla użytkownika %s.",
            self.request.user.username,
        )
        return ctx
