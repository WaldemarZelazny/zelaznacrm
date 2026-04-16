"""Formularze aplikacji deals."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Field, Layout, Row, Submit

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.leads.models import Lead

from .models import Deal


class DealForm(forms.ModelForm):
    """Formularz tworzenia i edycji umowy z layoutem Tabler/Bootstrap 5.

    Pole company wyswietla firmy dostepne dla zalogowanego uzytkownika.
    Pole lead filtruje leady powiazane z dostepnymi firmami.
    Wymaga przekazania parametru user= przy inicjalizacji.
    """

    class Meta:
        model = Deal
        fields = [
            "title",
            "company",
            "lead",
            "value",
            "close_date",
            "description",
        ]
        widgets = {
            "close_date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
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
                self.fields["lead"].queryset = Lead.objects.select_related(
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

        self.fields["lead"].required = False
        self.fields["lead"].empty_label = _("— bez leada zrodlowego —")

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
                        Field("lead", css_class="form-select"),
                        css_class="col-md-6",
                    ),
                ),
                css_class="mb-3",
            ),
            # Sekcja: Wartość i termin
            Div(
                Row(
                    Column(
                        Field("value", css_class="form-control"),
                        css_class="col-md-6",
                    ),
                    Column(
                        Field("close_date", css_class="form-control"),
                        css_class="col-md-6",
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
                _("Zapisz umowe"),
                css_class="btn btn-primary",
            ),
        )
