"""Widoki aplikacji companies - CRUD dla firm."""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.accounts.models import UserProfile

from .forms import CompanyForm
from .models import Company

logger = logging.getLogger(__name__)


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


class CompanyListView(LoginRequiredMixin, ListView):
    """Lista firm z filtrowaniem i paginacja.

    ADMIN widzi wszystkie firmy.
    HANDLOWIEC widzi tylko firmy, w ktorych jest opiekunem.
    Filtrowanie przez parametry GET: name, city, industry.
    """

    model = Company
    template_name = "companies/company_list.html"
    context_object_name = "companies"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem do wlasciciela."""
        qs = Company.objects.select_related("owner").order_by("name")
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        name = self.request.GET.get("name", "").strip()
        city = self.request.GET.get("city", "").strip()
        industry = self.request.GET.get("industry", "").strip()
        if name:
            qs = qs.filter(name__icontains=name)
        if city:
            qs = qs.filter(city__icontains=city)
        if industry:
            qs = qs.filter(industry=industry)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        """Dodaje do kontekstu wartosci filtrow i dostepne branze."""
        ctx = super().get_context_data(**kwargs)
        ctx["filter_name"] = self.request.GET.get("name", "")
        ctx["filter_city"] = self.request.GET.get("city", "")
        ctx["filter_industry"] = self.request.GET.get("industry", "")
        ctx["industry_choices"] = Company.Industry.choices
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class CompanyDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok firmy z powiazanymi obiektami (N+1 safe)."""

    model = Company
    template_name = "companies/company_detail.html"
    context_object_name = "company"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje firmy."""
        qs = Company.objects.prefetch_related(
            "contacts",
            "leads",
            "tasks",
            "company_notes",
            "documents",
        ).select_related("owner")
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


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Widok tworzenia nowej firmy. Owner ustawiany automatycznie."""

    model = Company
    form_class = CompanyForm
    template_name = "companies/company_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        logger.info(
            "Uzytkownik %s utworzyl firme: %s (id=%s)",
            self.request.user.username,
            self.object.name,
            self.object.pk,
        )
        messages.success(self.request, 'Firma "%s" zostala dodana.' % self.object.name)
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("companies:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj nowa firme"
        return ctx


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji firmy. Tylko wlasciciel lub ADMIN."""

    model = Company
    form_class = CompanyForm
    template_name = "companies/company_form.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user) and obj.owner != self.request.user:
            raise PermissionDenied(
                "Mozesz edytowac tylko firmy, ktorych jestes opiekunem."
            )
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            "Uzytkownik %s zaktualizowal firme: %s (id=%s)",
            self.request.user.username,
            self.object.name,
            self.object.pk,
        )
        messages.success(
            self.request, 'Firma "%s" zostala zaktualizowana.' % self.object.name
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("companies:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj: %s" % self.object.name
        return ctx


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania firmy. Tylko ADMIN."""

    model = Company
    template_name = "companies/company_confirm_delete.html"
    success_url = reverse_lazy("companies:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user):
            raise PermissionDenied(
                "Usuwanie firm jest zarezerwowane dla administratorow."
            )
        return obj

    def form_valid(self, form):
        company_name = self.object.name
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunał firme: %s",
            self.request.user.username,
            company_name,
        )
        messages.warning(self.request, 'Firma "%s" zostala usunieta.' % company_name)
        return response
