"""Widoki aplikacji notes – CRUD notatek CRM."""

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
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead
from apps.reports.models import ActivityLog

from .forms import NoteForm
from .models import Note

logger = logging.getLogger(__name__)


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


def _can_edit_note(user, note: Note) -> bool:
    """Sprawdza czy uzytkownik moze edytowac/usunac notatke (autor lub ADMIN)."""
    return _is_admin(user) or note.author == user


class NoteListView(LoginRequiredMixin, ListView):
    """Lista notatek z filtrowaniem i paginacja.

    ADMIN widzi wszystkie notatki.
    HANDLOWIEC widzi tylko notatki, ktorych jest autorem.
    Filtrowanie przez GET: company (nazwa), lead/deal/contact (pk).
    """

    model = Note
    template_name = "notes/note_list.html"
    context_object_name = "notes"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem per rola."""
        qs = Note.objects.select_related(
            "author", "company", "lead", "deal", "contact"
        ).order_by("-created_at")
        if not _is_admin(self.request.user):
            qs = qs.filter(author=self.request.user)
        company = self.request.GET.get("company", "").strip()
        lead_id = self.request.GET.get("lead", "").strip()
        deal_id = self.request.GET.get("deal", "").strip()
        contact_id = self.request.GET.get("contact", "").strip()
        if company:
            qs = qs.filter(company__name__icontains=company)
        if lead_id:
            qs = qs.filter(lead__pk=lead_id)
        if deal_id:
            qs = qs.filter(deal__pk=deal_id)
        if contact_id:
            qs = qs.filter(contact__pk=contact_id)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["filter_company"] = self.request.GET.get("company", "")
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class NoteDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok notatki z pelna trescia i powiazanymi obiektami."""

    model = Note
    template_name = "notes/note_detail.html"
    context_object_name = "note"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje notatki."""
        qs = Note.objects.select_related("author", "company", "lead", "deal", "contact")
        if not _is_admin(self.request.user):
            qs = qs.filter(author=self.request.user)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        ctx["can_edit"] = _can_edit_note(self.request.user, self.object)
        return ctx


class NoteCreateView(LoginRequiredMixin, CreateView):
    """Widok tworzenia nowej notatki.

    author ustawiany automatycznie na request.user.
    Opcjonalne pre-wypelnienie company/lead/deal/contact z parametrow GET.
    """

    model = Note
    form_class = NoteForm
    template_name = "notes/note_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        """Wstepnie wypelnia pola z parametrow GET."""
        initial = super().get_initial()
        user = self.request.user
        is_admin = _is_admin(user)

        company_id = self.request.GET.get("company_id")
        lead_id = self.request.GET.get("lead_id")
        deal_id = self.request.GET.get("deal_id")
        contact_id = self.request.GET.get("contact_id")

        if company_id:
            try:
                qs = (
                    Company.objects.all()
                    if is_admin
                    else Company.objects.filter(owner=user)
                )
                initial["company"] = qs.get(pk=company_id)
            except Company.DoesNotExist:
                pass
        if lead_id:
            try:
                qs = Lead.objects.all() if is_admin else Lead.objects.filter(owner=user)
                lead = qs.get(pk=lead_id)
                initial["lead"] = lead
                if "company" not in initial:
                    initial["company"] = lead.company
            except Lead.DoesNotExist:
                pass
        if deal_id:
            try:
                qs = Deal.objects.all() if is_admin else Deal.objects.filter(owner=user)
                deal = qs.get(pk=deal_id)
                initial["deal"] = deal
                if "company" not in initial:
                    initial["company"] = deal.company
            except Deal.DoesNotExist:
                pass
        if contact_id:
            try:
                # Kontakty sa dostepne dla wszystkich zalogowanych
                contact = Contact.objects.select_related("company").get(pk=contact_id)
                initial["contact"] = contact
                if "company" not in initial:
                    initial["company"] = contact.company
            except Contact.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s dodal notatke (id=%s)",
            self.request.user.username,
            self.object.pk,
        )
        messages.success(self.request, "Notatka zostala dodana.")
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("notes:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj notatke"
        return ctx


class NoteUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji notatki. Tylko autor lub ADMIN."""

    model = Note
    form_class = NoteForm
    template_name = "notes/note_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _can_edit_note(self.request.user, obj):
            raise PermissionDenied(
                "Mozesz edytowac tylko notatki, ktore sam napisalec."
            )
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            "Uzytkownik %s zaktualizowal notatke (id=%s)",
            self.request.user.username,
            self.object.pk,
        )
        messages.success(self.request, "Notatka zostala zaktualizowana.")
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("notes:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj notatke"
        return ctx


class NoteDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania notatki. Tylko autor lub ADMIN."""

    model = Note
    template_name = "notes/note_confirm_delete.html"
    success_url = reverse_lazy("notes:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _can_edit_note(self.request.user, obj):
            raise PermissionDenied("Mozesz usuwac tylko notatki, ktore sam napisalec.")
        return obj

    def form_valid(self, form):
        note_pk = self.object.pk
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunął notatke (id=%s)",
            self.request.user.username,
            note_pk,
        )
        messages.warning(self.request, "Notatka zostala usunieta.")
        return response
