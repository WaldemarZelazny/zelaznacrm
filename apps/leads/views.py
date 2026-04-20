"""Widoki aplikacji leads – lejek sprzedazowy CRUD i Kanban."""

from __future__ import annotations

import io
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.accounts.models import UserProfile
from apps.reports.models import ActivityLog

from .forms import LeadForm
from .models import Lead, WorkflowStage

logger = logging.getLogger(__name__)

_XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


class LeadListView(LoginRequiredMixin, ListView):
    """Lista leadow z filtrowaniem i paginacja.

    ADMIN widzi wszystkie leady.
    HANDLOWIEC widzi tylko leady, ktorych jest opiekunem.
    Filtrowanie przez parametry GET: status, source, stage.
    """

    model = Lead
    template_name = "leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem do wlasciciela."""
        qs = Lead.objects.select_related(
            "company", "owner", "stage", "contact"
        ).order_by("-created_at")
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        status = self.request.GET.get("status", "").strip()
        source = self.request.GET.get("source", "").strip()
        stage = self.request.GET.get("stage", "").strip()
        if status:
            qs = qs.filter(status=status)
        if source:
            qs = qs.filter(source=source)
        if stage:
            qs = qs.filter(stage__pk=stage)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        """Dodaje do kontekstu wartosci filtrow i dostepne opcje."""
        ctx = super().get_context_data(**kwargs)
        ctx["filter_status"] = self.request.GET.get("status", "")
        ctx["filter_source"] = self.request.GET.get("source", "")
        ctx["filter_stage"] = self.request.GET.get("stage", "")
        ctx["status_choices"] = Lead.Status.choices
        ctx["source_choices"] = Lead.Source.choices
        ctx["stages"] = WorkflowStage.objects.filter(is_active=True).order_by("order")
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class LeadKanbanView(LoginRequiredMixin, TemplateView):
    """Widok Kanban lejka sprzedazowego pogrupowany po etapach.

    Kola tablicy Kanban odpowiadaja aktywnym etapom WorkflowStage.
    HANDLOWIEC widzi tylko swoje leady, ADMIN widzi wszystkie.
    Pokazuje wylacznie leady otwarte (status NOWY lub W_TOKU).
    """

    template_name = "leads/lead_kanban.html"

    def get_context_data(self, **kwargs) -> dict:
        """Buduje slownik {stage: [leads]} dla renderowania kolumn."""
        ctx = super().get_context_data(**kwargs)
        stages = WorkflowStage.objects.filter(is_active=True).order_by("order")
        user = self.request.user
        is_admin = _is_admin(user)

        open_statuses = (Lead.Status.NOWY, Lead.Status.W_TOKU)
        base_qs = Lead.objects.filter(status__in=open_statuses).select_related(
            "company", "owner", "contact"
        )
        if not is_admin:
            base_qs = base_qs.filter(owner=user)

        # Buduj slownik etap -> lista leadow
        kanban_columns = []
        for stage in stages:
            leads = list(base_qs.filter(stage=stage))
            kanban_columns.append(
                {
                    "stage": stage,
                    "leads": leads,
                    "total_value": sum(lead.value for lead in leads),
                }
            )

        ctx["kanban_columns"] = kanban_columns
        ctx["is_admin"] = is_admin
        return ctx


class LeadDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok leada z powiazanymi zadaniami, notatkami, dokumentami."""

    model = Lead
    template_name = "leads/lead_detail.html"
    context_object_name = "lead"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje leady."""
        qs = Lead.objects.prefetch_related(
            "tasks",
            "notes",
            "documents",
        ).select_related("company", "contact", "owner", "stage")
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        ctx["can_edit"] = _is_admin(self.request.user) or (
            self.object.owner == self.request.user
        )
        ctx["closing_statuses"] = [
            Lead.Status.WYGRANA,
            Lead.Status.PRZEGRANA,
            Lead.Status.ANULOWANY,
        ]
        return ctx


class LeadCreateView(LoginRequiredMixin, CreateView):
    """Widok tworzenia nowego leada. Owner ustawiany automatycznie."""

    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form) -> HttpResponse:
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s utworzyl lead: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Lead "%s" zostal dodany.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("leads:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj nowy lead"
        return ctx


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji leada. Tylko wlasciciel lub ADMIN."""

    model = Lead
    form_class = LeadForm
    template_name = "leads/lead_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user) and obj.owner != self.request.user:
            raise PermissionDenied(
                "Mozesz edytowac tylko leady, ktorych jestes opiekunem."
            )
        return obj

    def form_valid(self, form) -> HttpResponse:
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.ZAKTUALIZOWANO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s zaktualizowal lead: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Lead "%s" zostal zaktualizowany.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("leads:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj: %s" % self.object.title
        return ctx


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania leada. Tylko ADMIN."""

    model = Lead
    template_name = "leads/lead_confirm_delete.html"
    success_url = reverse_lazy("leads:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user):
            raise PermissionDenied(
                "Usuwanie leadow jest zarezerwowane dla administratorow."
            )
        return obj

    def form_valid(self, form) -> HttpResponse:
        lead_title = self.object.title
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunál lead: %s",
            self.request.user.username,
            lead_title,
        )
        messages.warning(
            self.request,
            'Lead "%s" zostal usuniety.' % lead_title,
        )
        return response


class LeadCloseView(LoginRequiredMixin, View):
    """Widok zamkniecia leada (POST). Wywoluje lead.close(status).

    Dostep: tylko wlasciciel leada lub ADMIN.
    Parametr POST: close_status (WYGRANA / PRZEGRANA / ANULOWANY).
    """

    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)
        if not _is_admin(request.user) and lead.owner != request.user:
            raise PermissionDenied(
                "Mozesz zamknac tylko leady, ktorych jestes opiekunem."
            )
        close_status = request.POST.get("close_status", "").strip()
        try:
            lead.close(close_status)
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.Action.ZAKTUALIZOWANO,
                obj=lead,
            )
            messages.success(
                request,
                'Lead "%s" zostal zamkniety ze statusem: %s.'
                % (lead.title, lead.get_status_display()),
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return HttpResponseRedirect(reverse("leads:detail", kwargs={"pk": pk}))


class LeadExportView(LoginRequiredMixin, View):
    """Eksportuje liste leadow do pliku XLSX (openpyxl).

    ADMIN eksportuje wszystkie leady.
    HANDLOWIEC eksportuje tylko swoje leady.
    GET /leads/export/xlsx/
    """

    def get(self, request, *args, **kwargs):
        """Generuje plik XLSX i zwraca jako zalacznik do pobrania."""
        from datetime import date

        import openpyxl  # lazy

        qs = Lead.objects.select_related(
            "company", "owner", "stage", "contact"
        ).order_by("-created_at")
        if not _is_admin(request.user):
            qs = qs.filter(owner=request.user)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Leady"

        headers = [
            "ID",
            "Tytuł",
            "Firma",
            "Kontakt",
            "Opiekun",
            "Status",
            "Źródło",
            "Wartość (PLN)",
            "Etap",
            "Data utworzenia",
            "Data zamknięcia",
        ]
        ws.append(headers)

        for lead in qs:
            ws.append(
                [
                    lead.pk,
                    lead.title,
                    lead.company.name if lead.company else "",
                    str(lead.contact) if lead.contact else "",
                    (
                        lead.owner.get_full_name() or lead.owner.username
                        if lead.owner
                        else ""
                    ),
                    lead.get_status_display(),
                    lead.get_source_display() if lead.source else "",
                    float(lead.value) if lead.value else 0,
                    str(lead.stage) if lead.stage else "",
                    lead.created_at.strftime("%Y-%m-%d") if lead.created_at else "",
                    lead.closed_at.strftime("%Y-%m-%d") if lead.closed_at else "",
                ]
            )

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f"leady_{date.today().isoformat()}.xlsx"
        response = HttpResponse(
            buffer.read(),
            content_type=_XLSX_CONTENT_TYPE,
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        logger.info(
            "Uzytkownik %s eksportowal leady do XLSX (%d rekordow)",
            request.user.username,
            qs.count(),
        )
        return response
