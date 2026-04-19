"""Formularze aplikacji reports – filtry widokow raportow."""

from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ActivityLog


class ActivityLogFilterForm(forms.Form):
    """Formularz filtrowania logow aktywnosci (GET).

    Wszystkie pola opcjonalne – pusty formularz zwraca wszystkie logi.
    """

    action = forms.ChoiceField(
        choices=[("", _("Wszystkie akcje"))] + ActivityLog.Action.choices,
        required=False,
        label=_("Akcja"),
    )
    model_name = forms.CharField(
        max_length=100,
        required=False,
        label=_("Model"),
    )
    user = forms.CharField(
        max_length=150,
        required=False,
        label=_("Uzytkownik (login)"),
    )
