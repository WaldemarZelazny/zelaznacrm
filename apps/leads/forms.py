"""Formularze aplikacji leads."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Field, Layout, Row, Submit

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.contacts.models import Contact

from .models import Lead, WorkflowStage


class LeadForm(forms.ModelForm):
    """Formularz tworzenia i edycji leada z layoutem Tabler/Bootstrap 5.

    Pole company wyswietla firmy dostepne dla zalogowanego uzytkownika.
    Pole contact filtruje kontakty z wybranej firmy (lub wszystkie dostepne).
    Wymaga przekazania parametru user= przy inicjalizacji.
    """

    class Meta:
        model = Lead
        fields = [
            "title",
            "company",
            "contact",
            "source",
            "value",
            "stage",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs) -> None:
        """Konfiguruje helper crispy-forms oraz querysety dla pol FK."""
        super().__init__(*args, **kwargs)

        if user is not None:
            try:
                from apps.accounts.models import UserProfile

                is_admin = user.profile.role == UserProfile.Role.ADMIN
            except Exception:
                is_admin = False

            if is_admin:
                self.fields["company"].queryset = Company.objects.order_by("name")
                self.fields["contact"].queryset = Contact.objects.select_related(
                    "company"
                ).order_by("last_name", "first_name")
            else:
                self.fields["company"].queryset = Company.objects.filter(
                    owner=user
                ).order_by("name")
                self.fields["contact"].queryset = (
                    Contact.objects.filter(owner=user)
                    .select_related("company")
                    .order_by("last_name", "first_name")
                )

        self.fields["contact"].required = False
        self.fields["contact"].empty_label = _("— brak kontaktu —")
        self.fields["stage"].queryset = WorkflowStage.objects.filter(
            is_active=True
        ).order_by("order")

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
                        Field("company", css_class="form-select"),
                        css_class="col-md-6",
                    ),
                    Column(
                        Field("contact", css_class="form-select"),
                        css_class="col-md-6",
                    ),
                ),
                css_class="mb-3",
            ),
            # Sekcja: Parametry leada
            Div(
                Row(
                    Column(
                        Field("stage", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("source", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("value", css_class="form-control"),
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
                _("Zapisz lead"),
                css_class="btn btn-primary",
            ),
        )
