"""Widoki aplikacji reports."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.views.generic import ListView, TemplateView

from apps.accounts.models import UserProfile
from apps.deals.models import Deal
from apps.leads.models import Lead

from .models import ActivityLog


def _is_admin(user) -> bool:
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


class ReportsDashboardView(LoginRequiredMixin, TemplateView):
    """Strona glowna raportow z wykresami KPI.

    Dostepna tylko dla ADMIN.
    Dane dla Chart.js przekazywane jako JSON w kontekscie:
      - liczba leadow per status (ostatnie 30 dni)
      - liczba umow per status
      - top 5 handlowcow po liczbie wygranch leadow
      - wartosc umow per miesiac (ostatnie 6 miesiecy)
    """

    template_name = "reports/reports_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _is_admin(request.user):
            raise PermissionDenied("Dostep tylko dla administratorow.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)

        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        six_months_ago = today - timedelta(days=180)

        # 1. Liczba leadow per status (ostatnie 30 dni)
        leads_by_status = (
            Lead.objects.filter(created_at__date__gte=thirty_days_ago)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        lead_status_labels = [item["status"] for item in leads_by_status]
        lead_status_data = [item["count"] for item in leads_by_status]

        # 2. Liczba umow per status
        deals_by_status = (
            Deal.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        deal_status_labels = [item["status"] for item in deals_by_status]
        deal_status_data = [item["count"] for item in deals_by_status]

        # 3. Top 5 handlowcow po liczbie zamknietych leadow (WYGRANA)
        top_handlowcy = (
            Lead.objects.filter(status=Lead.Status.WYGRANA)
            .values("owner__username", "owner__first_name", "owner__last_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        top_labels = []
        for item in top_handlowcy:
            full = (
                (item["owner__first_name"] or "")
                + " "
                + (item["owner__last_name"] or "")
            ).strip()
            top_labels.append(full or item["owner__username"] or "no-name")
        top_data = [item["count"] for item in top_handlowcy]

        # 4. Wartosc umow per miesiac (ostatnie 6 miesiecy)
        deals_monthly = (
            Deal.objects.filter(created_at__date__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum("value"))
            .order_by("month")
        )
        monthly_labels = [item["month"].strftime("%Y-%m") for item in deals_monthly]
        monthly_data = [float(item["total"] or 0) for item in deals_monthly]

        # KPI summary
        ctx["kpi_leads_total"] = Lead.objects.count()
        ctx["kpi_leads_won"] = Lead.objects.filter(status=Lead.Status.WYGRANA).count()
        ctx["kpi_deals_total"] = Deal.objects.count()
        ctx["kpi_deals_value"] = Deal.objects.aggregate(total=Sum("value"))[
            "total"
        ] or Decimal("0")

        ctx["chart_lead_status"] = json.dumps(
            {"labels": lead_status_labels, "data": lead_status_data}
        )
        ctx["chart_deal_status"] = json.dumps(
            {"labels": deal_status_labels, "data": deal_status_data}
        )
        ctx["chart_top_handlowcy"] = json.dumps(
            {"labels": top_labels, "data": top_data}
        )
        ctx["chart_monthly_value"] = json.dumps(
            {"labels": monthly_labels, "data": monthly_data}
        )
        ctx["is_admin"] = True
        return ctx


class ActivityLogListView(LoginRequiredMixin, ListView):
    """Lista logow aktywnosci z filtrowaniem i paginacja.

    Dostepna tylko dla ADMIN.
    Filtrowanie przez GET: action, model_name, user (username).
    """

    model = ActivityLog
    template_name = "reports/activity_log_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _is_admin(request.user):
            raise PermissionDenied("Dostep tylko dla administratorow.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Buduje queryset z filtrowaniem."""
        qs = ActivityLog.objects.select_related("user").order_by("-created_at")
        action = self.request.GET.get("action", "").strip()
        model_name = self.request.GET.get("model_name", "").strip()
        username = self.request.GET.get("user", "").strip()
        if action:
            qs = qs.filter(action=action)
        if model_name:
            qs = qs.filter(model_name__icontains=model_name)
        if username:
            qs = qs.filter(user__username__icontains=username)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["filter_action"] = self.request.GET.get("action", "")
        ctx["filter_model"] = self.request.GET.get("model_name", "")
        ctx["filter_user"] = self.request.GET.get("user", "")
        ctx["action_choices"] = ActivityLog.Action.choices
        ctx["is_admin"] = True
        return ctx


class SalesReportView(LoginRequiredMixin, TemplateView):
    """Raport sprzedazowy per handlowiec.

    Dostepna tylko dla ADMIN.
    Dla kazdego handlowca: liczba leadow ogolnie i wygranych,
    liczba umow, suma wartosci, wskaznik konwersji.
    """

    template_name = "reports/sales_report.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _is_admin(request.user):
            raise PermissionDenied("Dostep tylko dla administratorow.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)

        handlowcy = (
            User.objects.filter(profile__role=UserProfile.Role.HANDLOWIEC)
            .select_related("profile")
            .order_by("last_name", "first_name")
        )

        rows = []
        for user in handlowcy:
            leads_total = Lead.objects.filter(owner=user).count()
            leads_won = Lead.objects.filter(
                owner=user, status=Lead.Status.WYGRANA
            ).count()
            deals_total = Deal.objects.filter(owner=user).count()
            deals_value = Deal.objects.filter(owner=user).aggregate(total=Sum("value"))[
                "total"
            ] or Decimal("0")
            conversion = (
                round(leads_won / leads_total * 100, 1) if leads_total > 0 else 0.0
            )
            rows.append(
                {
                    "user": user,
                    "leads_total": leads_total,
                    "leads_won": leads_won,
                    "deals_total": deals_total,
                    "deals_value": deals_value,
                    "conversion": conversion,
                }
            )

        rows.sort(key=lambda r: r["deals_value"], reverse=True)
        ctx["rows"] = rows
        ctx["is_admin"] = True
        return ctx
