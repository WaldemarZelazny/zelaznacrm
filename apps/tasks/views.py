"""Widoki aplikacji tasks – CRUD i kalendarz zadan."""

from __future__ import annotations

import io
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
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
from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead
from apps.reports.models import ActivityLog

from .forms import TaskForm
from .models import Task

logger = logging.getLogger(__name__)

# Kolory na kalendarzu FullCalendar per priorytet
_PRIORITY_COLOR = {
    Task.Priority.NISKI: "#6c757d",
    Task.Priority.SREDNI: "#0d6efd",
    Task.Priority.WYSOKI: "#fd7e14",
    Task.Priority.PILNY: "#dc3545",
}


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


def _can_edit_task(user, task: Task) -> bool:
    """Sprawdza czy uzytkownik moze edytowac zadanie."""
    return _is_admin(user) or task.assigned_to == user


class TaskListView(LoginRequiredMixin, ListView):
    """Lista zadan z filtrowaniem i paginacja.

    ADMIN widzi wszystkie zadania.
    HANDLOWIEC widzi tylko zadania przypisane do siebie.
    Filtrowanie przez parametry GET: status, priority, task_type.
    """

    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem do przypisanego."""
        qs = Task.objects.select_related(
            "assigned_to", "company", "lead", "deal"
        ).order_by("due_date", "-priority")
        if not _is_admin(self.request.user):
            qs = qs.filter(assigned_to=self.request.user)
        status = self.request.GET.get("status", "").strip()
        priority = self.request.GET.get("priority", "").strip()
        task_type = self.request.GET.get("task_type", "").strip()
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if task_type:
            qs = qs.filter(task_type=task_type)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["filter_status"] = self.request.GET.get("status", "")
        ctx["filter_priority"] = self.request.GET.get("priority", "")
        ctx["filter_task_type"] = self.request.GET.get("task_type", "")
        ctx["status_choices"] = Task.Status.choices
        ctx["priority_choices"] = Task.Priority.choices
        ctx["task_type_choices"] = Task.TaskType.choices
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class TaskCalendarView(LoginRequiredMixin, TemplateView):
    """Widok kalendarza zadan (strona HTML + JSON endpoint).

    GET /tasks/calendar/ – renderuje strone z FullCalendar.
    GET /tasks/calendar/?format=json – zwraca zdarzenia w formacie JSON.
    """

    template_name = "tasks/task_calendar.html"

    def _get_tasks_qs(self) -> QuerySet:
        """Buduje queryset zadan dla zalogowanego uzytkownika."""
        qs = Task.objects.select_related("assigned_to", "company", "lead", "deal")
        if not _is_admin(self.request.user):
            qs = qs.filter(assigned_to=self.request.user)
        return qs

    def get(self, request, *args, **kwargs):
        """Obsuguje GET: JSON dla FullCalendar lub HTML strony kalendarza."""
        if request.GET.get("format") == "json":
            return self._json_response()
        return super().get(request, *args, **kwargs)

    def _json_response(self) -> JsonResponse:
        """Zwraca zdarzenia FullCalendar jako JSON."""
        events = []
        for task in self._get_tasks_qs():
            # FullCalendar wymaga ISO 8601
            start = task.due_date.isoformat()
            color = _PRIORITY_COLOR.get(task.priority, "#6c757d")
            title = "[%s] %s" % (task.get_task_type_display(), task.title)
            events.append(
                {
                    "id": task.pk,
                    "title": title,
                    "start": start,
                    "color": color,
                    "url": reverse("tasks:detail", kwargs={"pk": task.pk}),
                    "extendedProps": {
                        "status": task.get_status_display(),
                        "priority": task.get_priority_display(),
                    },
                }
            )
        return JsonResponse(events, safe=False)

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class TaskDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok zadania."""

    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje zadania."""
        qs = Task.objects.select_related(
            "assigned_to", "created_by", "company", "lead", "deal"
        )
        if not _is_admin(self.request.user):
            qs = qs.filter(assigned_to=self.request.user)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        ctx["can_edit"] = _can_edit_task(self.request.user, self.object)
        return ctx


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Widok tworzenia nowego zadania.

    assigned_to i created_by ustawiane domyslnie na request.user.
    Opcjonalne pre-wypelnienie lead/deal/company z parametrow GET.
    """

    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        """Wstepnie wypelnia pola z parametrow GET."""
        initial = super().get_initial()
        initial["assigned_to"] = self.request.user
        user = self.request.user
        is_admin = _is_admin(user)

        lead_id = self.request.GET.get("lead_id")
        deal_id = self.request.GET.get("deal_id")
        company_id = self.request.GET.get("company_id")

        if lead_id:
            try:
                qs = Lead.objects.all() if is_admin else Lead.objects.filter(owner=user)
                lead = qs.get(pk=lead_id)
                initial["lead"] = lead
                initial["company"] = lead.company
            except Lead.DoesNotExist:
                pass
        elif deal_id:
            try:
                qs = Deal.objects.all() if is_admin else Deal.objects.filter(owner=user)
                deal = qs.get(pk=deal_id)
                initial["deal"] = deal
                initial["company"] = deal.company
            except Deal.DoesNotExist:
                pass
        elif company_id:
            try:
                qs = (
                    Company.objects.all()
                    if is_admin
                    else Company.objects.filter(owner=user)
                )
                initial["company"] = qs.get(pk=company_id)
            except Company.DoesNotExist:
                pass

        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Jeśli nie przypisano do nikogo, przypisz do twórcy
        if not form.instance.assigned_to:
            form.instance.assigned_to = self.request.user
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s utworzyl zadanie: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Zadanie "%s" zostalo dodane.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("tasks:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj nowe zadanie"
        return ctx


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji zadania. Tylko przypisany uzytkownik lub ADMIN."""

    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _can_edit_task(self.request.user, obj):
            raise PermissionDenied(
                "Mozesz edytowac tylko zadania przypisane do Ciebie."
            )
        # Zapamiętaj oryginalną wartość przed _post_clean() formularza
        self._original_assigned_to = obj.assigned_to
        return obj

    def form_valid(self, form):
        # Nie-admin nie może przypadkowo odznaczyć przypisania — zachowaj starą wartość.
        # UWAGA: self.object.assigned_to jest już nadpisane przez _post_clean() formularza,
        # dlatego używamy wartości zapamiętanej wcześniej w get_object().
        if not form.cleaned_data.get("assigned_to") and not _is_admin(
            self.request.user
        ):
            form.instance.assigned_to = self._original_assigned_to
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.ZAKTUALIZOWANO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s zaktualizowal zadanie: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Zadanie "%s" zostalo zaktualizowane.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("tasks:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj: %s" % self.object.title
        return ctx


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania zadania. Tylko ADMIN."""

    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("tasks:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user):
            raise PermissionDenied(
                "Usuwanie zadan jest zarezerwowane dla administratorow."
            )
        return obj

    def form_valid(self, form):
        task_title = self.object.title
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunał zadanie: %s",
            self.request.user.username,
            task_title,
        )
        messages.warning(
            self.request,
            'Zadanie "%s" zostalo usuniete.' % task_title,
        )
        return response


class TaskCompleteView(LoginRequiredMixin, View):
    """Widok oznaczenia zadania jako wykonanego (POST).

    Wywoluje task.complete(). Dostep: przypisany uzytkownik lub ADMIN.
    """

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        if not _can_edit_task(request.user, task):
            raise PermissionDenied(
                "Mozesz zakonczyc tylko zadania przypisane do Ciebie."
            )
        try:
            task.complete()
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.Action.ZAKTUALIZOWANO,
                obj=task,
            )
            messages.success(
                request,
                'Zadanie "%s" zostalo oznaczone jako wykonane.' % task.title,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return HttpResponseRedirect(reverse("tasks:detail", kwargs={"pk": pk}))


class TaskCancelView(LoginRequiredMixin, View):
    """Widok anulowania zadania (POST).

    Wywoluje task.cancel(). Dostep: przypisany uzytkownik lub ADMIN.
    """

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        if not _can_edit_task(request.user, task):
            raise PermissionDenied(
                "Mozesz anulowaç tylko zadania przypisane do Ciebie."
            )
        try:
            task.cancel()
            messages.warning(
                request,
                'Zadanie "%s" zostalo anulowane.' % task.title,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return HttpResponseRedirect(reverse("tasks:detail", kwargs={"pk": pk}))


class TaskExportView(LoginRequiredMixin, View):
    """Eksportuje liste zadan do pliku XLSX (openpyxl).

    ADMIN eksportuje wszystkie zadania.
    HANDLOWIEC eksportuje tylko zadania przypisane do siebie.
    GET /tasks/export/xlsx/
    """

    def get(self, request, *args, **kwargs):
        """Generuje plik XLSX i zwraca jako zalacznik do pobrania."""
        from datetime import date

        import openpyxl  # lazy

        qs = Task.objects.select_related(
            "assigned_to", "created_by", "company", "lead", "deal"
        ).order_by("due_date", "-priority")
        if not _is_admin(request.user):
            qs = qs.filter(assigned_to=request.user)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Zadania"

        headers = [
            "ID",
            "Tytuł",
            "Typ",
            "Priorytet",
            "Status",
            "Termin",
            "Przypisany do",
            "Firma",
            "Lead",
            "Umowa",
            "Wykonano",
            "Data utworzenia",
        ]
        ws.append(headers)

        for task in qs:
            ws.append(
                [
                    task.pk,
                    task.title,
                    task.get_task_type_display(),
                    task.get_priority_display(),
                    task.get_status_display(),
                    task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "",
                    (
                        task.assigned_to.get_full_name() or task.assigned_to.username
                        if task.assigned_to
                        else ""
                    ),
                    task.company.name if task.company else "",
                    task.lead.title if task.lead else "",
                    task.deal.title if task.deal else "",
                    (
                        task.completed_at.strftime("%Y-%m-%d %H:%M")
                        if task.completed_at
                        else ""
                    ),
                    task.created_at.strftime("%Y-%m-%d") if task.created_at else "",
                ]
            )

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f"zadania_{date.today().isoformat()}.xlsx"
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        logger.info(
            "Uzytkownik %s eksportowal zadania do XLSX (%d rekordow)",
            request.user.username,
            qs.count(),
        )
        return response
