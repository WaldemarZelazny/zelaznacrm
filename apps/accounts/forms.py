"""Formularze aplikacji accounts – tworzenie i edycja uzytkownikow."""

from __future__ import annotations

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Row, Submit

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class UserCreateForm(UserCreationForm):
    """Formularz tworzenia nowego uzytkownika (ADMIN only).

    Rozszerza wbudowany UserCreationForm o pola profilu:
    role i phone.
    """

    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        initial=UserProfile.Role.HANDLOWIEC,
        label="Rola",
        required=True,
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefon",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "role",
            "phone",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                "Dane konta",
                Row("username", "email"),
                Row("first_name", "last_name"),
                Row("password1", "password2"),
            ),
            Fieldset(
                "Profil",
                Row("role", "phone"),
            ),
        )
        self.helper.add_input(
            Submit("submit", "Utworz uzytkownika", css_class="btn-primary")
        )


class UserUpdateForm(forms.ModelForm):
    """Formularz edycji danych uzytkownika.

    Zmienia dane konta (first_name, last_name, email) oraz pola profilu.
    Rola widoczna tylko gdy edytuje ADMIN (filtrowane w widoku przez
    przekazanie is_admin=True do konstruktora).
    """

    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        label="Rola",
        required=True,
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefon",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, is_admin: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_admin:
            # Handlowiec edytuje tylko swoje dane – rola niedostepna
            del self.fields["role"]
        # Wstepnie wypelnij pola profilu
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
                if "role" in self.fields:
                    self.fields["role"].initial = profile.role
                self.fields["phone"].initial = profile.phone
            except UserProfile.DoesNotExist:
                pass

        self.helper = FormHelper()
        self.helper.add_input(
            Submit("submit", "Zapisz zmiany", css_class="btn-primary")
        )
