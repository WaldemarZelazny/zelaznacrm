"""Formularze aplikacji contacts."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Field, Layout, Row, Submit

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.companies.models import Company

from .models import Contact


class ContactForm(forms.ModelForm):
    """Formularz tworzenia i edycji kontaktu z layoutem Tabler/Bootstrap 5.

    Pole company wyswietla tylko firmy dostepne dla zalogowanego uzytkownika:
    HANDLOWIEC widzi wylacznie swoje firmy, ADMIN widzi wszystkie.
    Wymaga przekazania parametru user= przy inicjalizacji.
    """

    class Meta:
        model = Contact
        fields = [
            "first_name",
            "last_name",
            "company",
            "position",
            "department",
            "email",
            "phone",
            "mobile",
            "notes",
            "is_active",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs) -> None:
        """Konfiguruje helper crispy-forms oraz queryset dla pola company."""
        super().__init__(*args, **kwargs)

        if user is not None:
            try:
                from apps.accounts.models import UserProfile

                if user.profile.role == UserProfile.Role.ADMIN:
                    self.fields["company"].queryset = Company.objects.order_by("name")
                else:
                    self.fields["company"].queryset = Company.objects.filter(
                        owner=user
                    ).order_by("name")
            except Exception:
                self.fields["company"].queryset = Company.objects.filter(
                    owner=user
                ).order_by("name")

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "form"
        self.helper.attrs = {"novalidate": True}

        self.helper.layout = Layout(
            # Sekcja: Dane osobowe
            Div(
                Row(
                    Column(
                        Field("first_name", css_class="form-control"),
                        css_class="col-md-6",
                    ),
                    Column(
                        Field("last_name", css_class="form-control"),
                        css_class="col-md-6",
                    ),
                ),
                Row(
                    Column(
                        Field("company", css_class="form-select"),
                        css_class="col-md-8",
                    ),
                    Column(
                        Field("department", css_class="form-select"),
                        css_class="col-md-4",
                    ),
                ),
                Field("position", css_class="form-control"),
                css_class="mb-3",
            ),
            # Sekcja: Dane kontaktowe
            Div(
                Row(
                    Column(
                        Field("email", css_class="form-control"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("phone", css_class="form-control"),
                        css_class="col-md-4",
                    ),
                    Column(
                        Field("mobile", css_class="form-control"),
                        css_class="col-md-4",
                    ),
                ),
                css_class="mb-3",
            ),
            # Sekcja: Uwagi i status
            Div(
                Field("notes", css_class="form-control"),
                Field("is_active"),
                css_class="mb-3",
            ),
            Submit(
                "submit",
                _("Zapisz kontakt"),
                css_class="btn btn-primary",
            ),
        )
