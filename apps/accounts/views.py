"""Widoki aplikacji accounts – uwierzytelnianie i profil użytkownika."""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

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
    """Profil zalogowanego użytkownika.

    Wyświetla dane konta i UserProfile (jeśli istnieje).
    """

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        """Dodaje profil użytkownika do kontekstu."""
        ctx = super().get_context_data(**kwargs)
        try:
            ctx["profile"] = self.request.user.userprofile
        except Exception:
            ctx["profile"] = None
        return ctx
