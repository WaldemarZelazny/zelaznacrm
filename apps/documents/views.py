"""Widoki aplikacji documents – CRUD i pobieranie plikow."""

from __future__ import annotations

import logging
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead
from apps.reports.models import ActivityLog

from .forms import DocumentForm
from .models import Document

logger = logging.getLogger(__name__)


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


def _can_edit_document(user, document: Document) -> bool:
    """Sprawdza czy uzytkownik moze edytowac dokument (tworca lub ADMIN)."""
    return _is_admin(user) or document.created_by == user


class DocumentListView(LoginRequiredMixin, ListView):
    """Lista dokumentow z filtrowaniem i paginacja.

    ADMIN widzi wszystkie dokumenty.
    HANDLOWIEC widzi tylko dokumenty, ktore sam wgral (created_by).
    Filtrowanie przez GET: doc_type, company (szukanie po nazwie).
    """

    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem per rola."""
        qs = Document.objects.select_related(
            "company", "lead", "deal", "created_by"
        ).order_by("-created_at")
        if not _is_admin(self.request.user):
            qs = qs.filter(created_by=self.request.user)
        doc_type = self.request.GET.get("doc_type", "").strip()
        company = self.request.GET.get("company", "").strip()
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        if company:
            qs = qs.filter(company__name__icontains=company)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["filter_doc_type"] = self.request.GET.get("doc_type", "")
        ctx["filter_company"] = self.request.GET.get("company", "")
        ctx["doc_type_choices"] = Document.DocType.choices
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok dokumentu z metadanymi i przyciskiem pobierania."""

    model = Document
    template_name = "documents/document_detail.html"
    context_object_name = "document"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje dokumenty."""
        qs = Document.objects.select_related("company", "lead", "deal", "created_by")
        if not _is_admin(self.request.user):
            qs = qs.filter(created_by=self.request.user)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        ctx["can_edit"] = _can_edit_document(self.request.user, self.object)
        return ctx


class DocumentCreateView(LoginRequiredMixin, CreateView):
    """Widok wgrywania nowego dokumentu.

    created_by ustawiany automatycznie na request.user.
    Opcjonalne pre-wypelnienie company/lead/deal z parametrow GET.
    """

    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

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
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.object,
        )
        logger.info(
            "Uzytkownik %s wgral dokument: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Dokument "%s" zostal dodany.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("documents:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj nowy dokument"
        return ctx


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji metadanych dokumentu. Tylko tworca lub ADMIN."""

    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _can_edit_document(self.request.user, obj):
            raise PermissionDenied(
                "Mozesz edytowac tylko dokumenty, ktore sam wgralec."
            )
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            "Uzytkownik %s zaktualizowal dokument: %s (id=%s)",
            self.request.user.username,
            self.object.title,
            self.object.pk,
        )
        messages.success(
            self.request,
            'Dokument "%s" zostal zaktualizowany.' % self.object.title,
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("documents:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj: %s" % self.object.title
        return ctx


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania dokumentu. Tylko ADMIN."""

    model = Document
    template_name = "documents/document_confirm_delete.html"
    success_url = reverse_lazy("documents:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user):
            raise PermissionDenied(
                "Usuwanie dokumentow jest zarezerwowane dla administratorow."
            )
        return obj

    def form_valid(self, form):
        doc_title = self.object.title
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunął dokument: %s",
            self.request.user.username,
            doc_title,
        )
        messages.warning(
            self.request,
            'Dokument "%s" zostal usuniety.' % doc_title,
        )
        return response


class DocumentDownloadView(LoginRequiredMixin, View):
    """Serwuje plik dokumentu do pobrania jako FileResponse.

    Dostep: kazdy zalogowany uzytkownik (LoginRequiredMixin).
    Jesli plik nie istnieje na dysku lub nie jest przypisany, zwraca 404.
    """

    def get(self, request, pk):
        """Obsuguje GET: wysyla plik jako zalacznik."""
        doc = get_object_or_404(Document, pk=pk)
        if not doc.file:
            raise Http404("Dokument nie ma przypisanego pliku.")
        try:
            file_handle = doc.file.open("rb")
        except (FileNotFoundError, OSError):
            raise Http404("Plik nie istnieje na serwerze.")
        filename = Path(doc.file.name).name
        response = FileResponse(file_handle, as_attachment=True, filename=filename)
        logger.info(
            "Uzytkownik %s pobral dokument: %s (id=%s)",
            request.user.username,
            doc.title,
            doc.pk,
        )
        return response
