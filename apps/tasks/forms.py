"""Formularze aplikacji tasks."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Field, Layout, Row, Submit

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead

from .models import Task


class TaskForm(forms.ModelForm):
    """Formularz tworzenia i edycji zadania z layoutem Tabler/Bootstrap 5.

    Pole due_date uzywa DateTimeInput (HTML5 datetime-local).
    Pole assigned_to pokazuje wszystkich aktywnych uzytkownikow.
    Pola company/lead/deal sa opcjonalne i filtrowane per rola uzytkownika.
    Wymaga przekazania parametru user= przy inicjalizacji.
    """

    class Meta:
        model = Task
        fields = [
            "title",
            "task_type",
            "priority",
            "status",
            "due_date",
            "assigned_to",
            "company",
            "lead",
            "deal",
            "description",
        ]
        widgets = {
            "due_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs) -> None:
        """Konfiguruje helper crispy-forms oraz querysety dla pol FK."""
        super().__init__(*args, **kwargs)

        # Formatowanie datetime-local wymaga specjalnej wartosci initial
        if self.instance and self.instance.pk and self.instance.due_date:
            self.initial["due_date"] = self.instance.due_date.strftime("%Y-%m-%dT%H:%M")

        self.fields["assigned_to"].queryset = User.objects.filter(
            is_active=True
        ).order_by("last_name", "first_name", "username")
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].empty_label = _("— nieprzypisane —")

        if user is not None:
            try:
                from apps.accounts.models import UserProfile

                is_admin = user.profile.role == UserProfile.Role.ADMIN
            except Exception:
                is_admin = False

            if is_admin:
                self.fields["company"].queryset = Company.objects.order_by("name")
                self.fields["lead"].queryset = Lead.objects.select_related(
                    "company"
                ).order_by("-created_at")
                self.fields["deal"].queryset = Deal.objects.select_related(
                    "company"
                ).order_by("-created_at")
            else:
                self.fields["company"].queryset = Company.objects.filter(
                    owner=user
                ).order_by("name")
                self.fields["lead"].queryset = (
                    Lead.objects.filter(owner=user)
                    .select_related("company")
                    .order_by("-created_at")
                )
                self.fields["deal"].queryset = (
                    Deal.objects.filter(owner=user)
                    .select_related("company")
                    .order_by("-created_at")
                )

        for field_name in ("company", "lead", "deal"):
            self.fields[field_name].required = False
            self.fields[field_name].empty_label = _("— brak —")

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "form"
        self.helper.attrs = {"novalidate": True}

        self.helper.layout = Layout(
            # Sekcja: Podstawowe dane
            Div(
                Field("title", css_class="form-control"),
                Row(
                    Column(
                        Field("task_type", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("priority", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("status", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                ),
                css_class="mb-3",
            ),
            # Sekcja: Termin i przypisanie
            Div(
                Row(
                    Column(
                        Field("due_date", css_class="form-control"),
                        css_class="col-md-6",
                    ),
                    Column(
                        Field("assigned_to", css_class="form-select"),
                        css_class="col-md-6",
                    ),
                ),
                css_class="mb-3",
            ),
            # Sekcja: Powiazania CRM
            Div(
                Row(
                    Column(
                        Field("company", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("lead", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("deal", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                ),
                css_class="mb-3",
            ),
            # Sekcja: Opis
            Div(
                Field("description", css_class="form-control"),
                css_class="mb-3",
            ),
            Submit(
                "submit",
                _("Zapisz zadanie"),
                css_class="btn btn-primary",
            ),
        )
