"""Formularze aplikacji companies."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Field, Layout, Row, Submit

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Company


class CompanyForm(forms.ModelForm):
    """Formularz tworzenia i edycji firmy z layoutem Tabler/Bootstrap 5.

    Używa crispy-forms do renderowania pól w układzie siatki Bootstrap.
    Pole owner jest ukryte – ustawiane automatycznie w widoku.
    """

    class Meta:
        model = Company
        fields = [
            "name",
            "nip",
            "industry",
            "phone",
            "email",
            "website",
            "address",
            "postal_code",
            "city",
            "notes",
            "is_active",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs) -> None:
        """Konfiguruje helper crispy-forms z layoutem Tabler."""
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "form"
        self.helper.attrs = {"novalidate": True}

        self.helper.layout = Layout(
            # Sekcja: Podstawowe dane
            Div(
                Row(
                    Column(
                        Field("name", css_class="form-control"), css_class="col-md-8"
                    ),
                    Column(
                        Field("industry", css_class="form-select"), css_class="col-md-4"
                    ),
                ),
                Row(
                    Column(
                        Field("nip", css_class="form-control"), css_class="col-md-4"
                    ),
                    Column(
                        Field("phone", css_class="form-control"), css_class="col-md-4"
                    ),
                    Column(
                        Field("email", css_class="form-control"), css_class="col-md-4"
                    ),
                ),
                Field("website", css_class="form-control"),
                css_class="mb-3",
            ),
            # Sekcja: Adres
            Div(
                Row(
                    Column(
                        Field("address", css_class="form-control"), css_class="col-md-6"
                    ),
                    Column(
                        Field("postal_code", css_class="form-control"),
                        css_class="col-md-2",
                    ),
                    Column(
                        Field("city", css_class="form-control"), css_class="col-md-4"
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
            # Przycisk zapisu
            Submit(
                "submit",
                _("Zapisz firmę"),
                css_class="btn btn-primary",
            ),
        )
