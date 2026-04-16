"""Widoki aplikacji accounts – uwierzytelnianie i profil uzytkownika."""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import UserCreateForm, UserUpdateForm
from .models import UserProfile

logger = logging.getLogger(__name__)


class LandingView(View):
    """Strona startowa – landing page dla niezalogowanych.

    Zalogowani użytkownicy są automatycznie przekierowani do dashboardu.
    """

    def get(self, request):
        """Wyświetla landing page lub przekierowuje zalogowanego użytkownika."""
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        return render(request, "base.html")


class LoginView(View):
    """Widok logowania z formularzem Django AuthenticationForm.

    GET  – wyświetla formularz logowania.
    POST – przetwarza dane i loguje użytkownika lub zwraca błędy.
    """

    template_name = "accounts/login.html"

    def get(self, request):
        """Wyświetla pusty formularz logowania."""
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        form = AuthenticationForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        """Przetwarza formularz logowania."""
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info("Użytkownik %s zalogował się.", user.username)
            messages.success(
                request, f"Witaj, {user.get_full_name() or user.username}!"
            )
            # Przekieruj na next lub domyślnie na dashboard
            next_url = request.GET.get("next", "")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect("dashboard:index")
        logger.warning(
            "Nieudana próba logowania: %s",
            request.POST.get("username", "—"),
        )
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    """Widok wylogowania — tylko POST (zabezpieczenie CSRF).

    Wylogowuje użytkownika i przekierowuje na stronę logowania.
    """

    def post(self, request):
        """Wylogowuje użytkownika."""
        username = request.user.username if request.user.is_authenticated else "—"
        logout(request)
        logger.info("Użytkownik %s wylogował się.", username)
        messages.info(request, "Zostałeś wylogowany.")
        return redirect("accounts:login")


class ProfileView(LoginRequiredMixin, TemplateView):
    """Profil zalogowanego uzytkownika.

    Wyswietla dane konta i UserProfile (jesli istnieje).
    """

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        """Dodaje profil uzytkownika do kontekstu."""
        ctx = super().get_context_data(**kwargs)
        try:
            ctx["profile"] = self.request.user.profile
        except UserProfile.DoesNotExist:
            ctx["profile"] = None
        return ctx


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


class UserListView(LoginRequiredMixin, ListView):
    """Lista wszystkich uzytkownikow systemu. Dostepna tylko dla ADMIN."""

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _is_admin(request.user):
            raise PermissionDenied("Dostep tylko dla administratorow.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.select_related("profile").order_by(
            "last_name", "first_name", "username"
        )

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = True
        return ctx


class UserDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy profil uzytkownika.

    Zalogowany uzytkownik widzi tylko swoj profil.
    ADMIN widzi dowolny profil.
    """

    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "viewed_user"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user) and obj != self.request.user:
            raise PermissionDenied("Mozesz ogladac tylko swoj profil.")
        return obj

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        ctx["can_edit"] = (
            _is_admin(self.request.user) or self.object == self.request.user
        )
        return ctx


class UserCreateView(LoginRequiredMixin, CreateView):
    """Tworzenie nowego uzytkownika. Dostepne tylko dla ADMIN."""

    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not _is_admin(request.user):
            raise PermissionDenied("Dostep tylko dla administratorow.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        profile = self.object.profile
        profile.role = form.cleaned_data.get("role", UserProfile.Role.HANDLOWIEC)
        profile.phone = form.cleaned_data.get("phone", "")
        profile.save()
        logger.info(
            "ADMIN %s utworzyl uzytkownika %s",
            self.request.user.username,
            self.object.username,
        )
        messages.success(
            self.request,
            f"Uzytkownik {self.object.username} zostal utworzony.",
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("accounts:user_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Nowy uzytkownik"
        ctx["is_admin"] = True
        return ctx


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """Edycja danych uzytkownika. Dostepna dla ADMIN lub wlasciciela profilu."""

    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user) and obj != self.request.user:
            raise PermissionDenied("Mozesz edytowac tylko swoj profil.")
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["is_admin"] = _is_admin(self.request.user)
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        profile = self.object.profile
        if _is_admin(self.request.user) and "role" in form.cleaned_data:
            profile.role = form.cleaned_data["role"]
        if "phone" in form.cleaned_data:
            profile.phone = form.cleaned_data.get("phone", "")
        profile.save()
        logger.info(
            "Uzytkownik %s zaktualizowal profil %s",
            self.request.user.username,
            self.object.username,
        )
        messages.success(self.request, "Dane uzytkownika zostaly zaktualizowane.")
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("accounts:user_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj uzytkownika"
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx
