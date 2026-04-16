"""Formularze aplikacji documents."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Field, Layout, Row, Submit

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead

from .models import Document


class DocumentForm(forms.ModelForm):
    """Formularz wgrywania i edycji dokumentu z layoutem Tabler/Bootstrap 5.

    Plik jest wymagany przy tworzeniu, opcjonalny przy edycji.
    Pola company/lead/deal sa opcjonalne i filtrowane per rola uzytkownika.
    Wymaga przekazania parametru user= przy inicjalizacji.
    """

    class Meta:
        model = Document
        fields = [
            "title",
            "doc_type",
            "file",
            "company",
            "lead",
            "deal",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs) -> None:
        """Konfiguruje helper crispy-forms, querysety FK i wymagalnosc pliku."""
        super().__init__(*args, **kwargs)

        # Plik wymagany tylko przy tworzeniu nowego dokumentu
        if self.instance and self.instance.pk:
            self.fields["file"].required = False
        else:
            self.fields["file"].required = True

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
        # enctype multipart wymagany do wgrywania plikow
        self.helper.attrs = {"novalidate": True, "enctype": "multipart/form-data"}

        self.helper.layout = Layout(
            # Sekcja: Tytul i rodzaj
            Div(
                Field("title", css_class="form-control"),
                Row(
                    Column(
                        Field("doc_type", css_class="form-select"),
                        css_class="col-md-6",
                    ),
                    Column(
                        Field("file", css_class="form-control"),
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
                _("Zapisz dokument"),
                css_class="btn btn-primary",
            ),
        )
