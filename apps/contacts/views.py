"""Widoki aplikacji contacts - CRUD dla kontaktow."""

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
from apps.companies.models import Company
from apps.reports.models import ActivityLog

from .forms import ContactForm
from .models import Contact

logger = logging.getLogger(__name__)


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


class ContactListView(LoginRequiredMixin, ListView):
    """Lista kontaktow z filtrowaniem i paginacja.

    ADMIN widzi wszystkie kontakty.
    HANDLOWIEC widzi tylko kontakty, ktorych jest opiekunem.
    Filtrowanie przez parametry GET: name, company, department.
    """

    model = Contact
    template_name = "contacts/contact_list.html"
    context_object_name = "contacts"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem do wlasciciela."""
        qs = Contact.objects.select_related("company", "owner").order_by(
            "last_name", "first_name"
        )
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        name = self.request.GET.get("name", "").strip()
        company = self.request.GET.get("company", "").strip()
        department = self.request.GET.get("department", "").strip()
        if name:
            qs = qs.filter(last_name__icontains=name) | qs.filter(
                first_name__icontains=name
            )
        if company:
            qs = qs.filter(company__name__icontains=company)
        if department:
            qs = qs.filter(department=department)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        """Dodaje do kontekstu wartosci filtrow i dostepne dzialy."""
        ctx = super().get_context_data(**kwargs)
        ctx["filter_name"] = self.request.GET.get("name", "")
        ctx["filter_company"] = self.request.GET.get("company", "")
        ctx["filter_department"] = self.request.GET.get("department", "")
        ctx["department_choices"] = Contact.Department.choices
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class ContactDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok kontaktu z powiazanymi notatkami."""

    model = Contact
    template_name = "contacts/contact_detail.html"
    context_object_name = "contact"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje kontakty."""
        qs = Contact.objects.prefetch_related("contact_notes").select_related(
            "company", "owner"
        )
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


class ContactCreateView(LoginRequiredMixin, CreateView):
    """Widok tworzenia nowego kontaktu. Owner ustawiany automatycznie."""

    model = Contact
    form_class = ContactForm
    template_name = "contacts/contact_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        """Wstepnie wypelnia pole company z parametru GET ?company_id=."""
        initial = super().get_initial()
        company_id = self.request.GET.get("company_id")
        if company_id:
            try:
                qs = Company.objects.all()
                if not _is_admin(self.request.user):
                    qs = qs.filter(owner=self.request.user)
                company = qs.get(pk=company_id)
                initial["company"] = company
            except Company.DoesNotExist:
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
            "Uzytkownik %s utworzyl kontakt: %s (id=%s)",
            self.request.user.username,
            self.object.full_name,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Kontakt "%s" zostal dodany.' % self.object.full_name,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("contacts:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj nowy kontakt"
        return ctx


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji kontaktu. Tylko wlasciciel lub ADMIN."""

    model = Contact
    form_class = ContactForm
    template_name = "contacts/contact_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user) and obj.owner != self.request.user:
            raise PermissionDenied(
                "Mozesz edytowac tylko kontakty, ktorych jestes opiekunem."
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
            "Uzytkownik %s zaktualizowal kontakt: %s (id=%s)",
            self.request.user.username,
            self.object.full_name,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Kontakt "%s" zostal zaktualizowany.' % self.object.full_name,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("contacts:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj: %s" % self.object.full_name
        return ctx


class ContactDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania kontaktu. Tylko ADMIN."""

    model = Contact
    template_name = "contacts/contact_confirm_delete.html"
    success_url = reverse_lazy("contacts:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user):
            raise PermissionDenied(
                "Usuwanie kontaktow jest zarezerwowane dla administratorow."
            )
        return obj

    def form_valid(self, form):
        contact_name = self.object.full_name
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.USUNIETO,
            obj=self.object,
        )
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunál kontakt: %s",
            self.request.user.username,
            contact_name,
        )
        messages.warning(
            self.request,
            'Kontakt "%s" zostal usuniety.' % contact_name,
        )
        return response
