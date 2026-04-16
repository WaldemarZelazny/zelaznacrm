"""Formularze aplikacji notes."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Field, Layout, Row, Submit

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead

from .models import Note


class NoteForm(forms.ModelForm):
    """Formularz tworzenia i edycji notatki z layoutem Tabler/Bootstrap 5.

    Pole content uzywa Textarea (min. 4 wiersze).
    Pola company/lead/deal/contact sa opcjonalne i filtrowane per rola.
    Wymaga przekazania parametru user= przy inicjalizacji.
    """

    class Meta:
        model = Note
        fields = [
            "content",
            "company",
            "lead",
            "deal",
            "contact",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
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
                self.fields["deal"].queryset = Deal.objects.select_related(
                    "company"
                ).order_by("-created_at")
                self.fields["contact"].queryset = Contact.objects.select_related(
                    "company"
                ).order_by("last_name", "first_name")
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
                # Kontakty powiazane z firmami uzytkownika
                self.fields["contact"].queryset = (
                    Contact.objects.filter(company__owner=user)
                    .select_related("company")
                    .order_by("last_name", "first_name")
                )

        for field_name in ("company", "lead", "deal", "contact"):
            self.fields[field_name].required = False
            self.fields[field_name].empty_label = _("— brak —")

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "form"
        self.helper.attrs = {"novalidate": True}

        self.helper.layout = Layout(
            # Tresc notatki
            Div(
                Field("content", css_class="form-control"),
                css_class="mb-3",
            ),
            # Powiazania CRM
            Div(
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
                Row(
                    Column(
                        Field("lead", css_class="form-select"),
                        css_class="col-md-6",
                    ),
                    Column(
                        Field("deal", css_class="form-select"),
                        css_class="col-md-6",
                    ),
                ),
                css_class="mb-3",
            ),
            Submit(
                "submit",
                _("Zapisz notatke"),
                css_class="btn btn-primary",
            ),
        )
