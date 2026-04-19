"""Widoki aplikacji deals – CRUD dla umow handlowych."""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.accounts.models import UserProfile
from apps.leads.models import Lead
from apps.reports.models import ActivityLog

from .forms import DealForm
from .models import Deal

logger = logging.getLogger(__name__)


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


class DealListView(LoginRequiredMixin, ListView):
    """Lista umow z filtrowaniem, paginacja i suma wartosci aktywnych.

    ADMIN widzi wszystkie umowy.
    HANDLOWIEC widzi tylko umowy, ktorych jest opiekunem.
    Filtrowanie przez parametry GET: status, company.
    """

    model = Deal
    template_name = "deals/deal_list.html"
    context_object_name = "deals"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem do wlasciciela."""
        qs = Deal.objects.select_related("company", "owner", "lead").order_by(
            "-created_at"
        )
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        status = self.request.GET.get("status", "").strip()
        company = self.request.GET.get("company", "").strip()
        if status:
            qs = qs.filter(status=status)
        if company:
            qs = qs.filter(company__name__icontains=company)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        """Dodaje filtry, statusy i sume wartosci aktywnych umow."""
        ctx = super().get_context_data(**kwargs)
        ctx["filter_status"] = self.request.GET.get("status", "")
        ctx["filter_company"] = self.request.GET.get("company", "")
        ctx["status_choices"] = Deal.Status.choices
        ctx["is_admin"] = _is_admin(self.request.user)

        # Suma wartosci aktywnych umow (nie tylko na biezacej stronie)
        active_qs = self.get_queryset().filter(status=Deal.Status.AKTYWNA)
        ctx["active_total"] = active_qs.aggregate(total=Sum("value"))["total"] or 0
        return ctx


class DealDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok umowy z powiazanymi zadaniami, notatkami, dokumentami."""

    model = Deal
    template_name = "deals/deal_detail.html"
    context_object_name = "deal"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje umowy."""
        qs = Deal.objects.prefetch_related(
            "tasks",
            "notes",
            "documents",
        ).select_related("company", "lead", "owner")
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        ctx["can_edit"] = _is_admin(self.request.user) or (
            self.object.owner == self.request.user
        )
        return ctx


class DealCreateView(LoginRequiredMixin, CreateView):
    """Widok tworzenia nowej umowy. Owner ustawiany automatycznie."""

    model = Deal
    form_class = DealForm
    template_name = "deals/deal_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        """Wstepnie wypelnia pole lead z parametru GET ?lead_id=."""
        initial = super().get_initial()
        lead_id = self.request.GET.get("lead_id")
        if lead_id:
            try:
                qs = Lead.objects.all()
                if not _is_admin(self.request.user):
                    qs = qs.filter(owner=self.request.user)
                lead = qs.get(pk=lead_id)
                initial["lead"] = lead
                initial["company"] = lead.company
            except Lead.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s utworzyl umowe: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Umowa "%s" zostala dodana.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("deals:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj nowa umowe"
        return ctx


class DealUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji umowy. Tylko wlasciciel lub ADMIN."""

    model = Deal
    form_class = DealForm
    template_name = "deals/deal_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user) and obj.owner != self.request.user:
            raise PermissionDenied(
                "Mozesz edytowac tylko umowy, ktorych jestes opiekunem."
            )
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.ZAKTUALIZOWANO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s zaktualizowal umowe: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Umowa "%s" zostala zaktualizowana.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("deals:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj: %s" % self.object.title
        return ctx


class DealDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania umowy. Tylko ADMIN."""

    model = Deal
    template_name = "deals/deal_confirm_delete.html"
    success_url = reverse_lazy("deals:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user):
            raise PermissionDenied(
                "Usuwanie umow jest zarezerwowane dla administratorow."
            )
        return obj

    def form_valid(self, form):
        deal_title = self.object.title
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunál umowe: %s",
            self.request.user.username,
            deal_title,
        )
        messages.warning(
            self.request,
            'Umowa "%s" zostala usunieta.' % deal_title,
        )
        return response


class DealCompleteView(LoginRequiredMixin, View):
    """Widok zatwierdzenia umowy jako zrealizowanej (POST).

    Wywoluje deal.complete(). Dostep: wlasciciel lub ADMIN.
    """

    def post(self, request, pk):
        deal = get_object_or_404(Deal, pk=pk)
        if not _is_admin(request.user) and deal.owner != request.user:
            raise PermissionDenied(
                "Mozesz zatwierdzac tylko umowy, ktorych jestes opiekunem."
            )
        try:
            deal.complete()
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.Action.ZAKTUALIZOWANO,
                obj=deal,
            )
            messages.success(
                request,
                'Umowa "%s" zostala oznaczona jako zrealizowana.' % deal.title,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return HttpResponseRedirect(reverse("deals:detail", kwargs={"pk": pk}))


class DealCancelView(LoginRequiredMixin, View):
    """Widok anulowania umowy (POST).

    Wywoluje deal.cancel(). Dostep: wlasciciel lub ADMIN.
    """

    def post(self, request, pk):
        deal = get_object_or_404(Deal, pk=pk)
        if not _is_admin(request.user) and deal.owner != request.user:
            raise PermissionDenied(
                "Mozesz anulowaæ tylko umowy, ktorych jestes opiekunem."
            )
        try:
            deal.cancel()
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.Action.ZAKTUALIZOWANO,
                obj=deal,
            )
            messages.warning(
                request,
                'Umowa "%s" zostala anulowana.' % deal.title,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return HttpResponseRedirect(reverse("deals:detail", kwargs={"pk": pk}))
