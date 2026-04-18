"""Widoki aplikacji companies - CRUD dla firm."""

from __future__ import annotations

import datetime
import json
import logging
from urllib.parse import urlencode

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from apps.accounts.models import UserProfile

from .forms import CompanyForm
from .models import Company

logger = logging.getLogger(__name__)


def _is_admin(user) -> bool:
    """Sprawdza czy uzytkownik ma role ADMIN."""
    try:
        return user.profile.role == UserProfile.Role.ADMIN
    except UserProfile.DoesNotExist:
        return False


class CompanyListView(LoginRequiredMixin, ListView):
    """Lista firm z filtrowaniem i paginacja.

    ADMIN widzi wszystkie firmy.
    HANDLOWIEC widzi tylko firmy, w ktorych jest opiekunem.
    Filtrowanie przez parametry GET: name, city, industry.
    """

    model = Company
    template_name = "companies/company_list.html"
    context_object_name = "companies"
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        """Buduje queryset z filtrowaniem i ograniczeniem do wlasciciela."""
        qs = Company.objects.select_related("owner").order_by("name")
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        name = self.request.GET.get("name", "").strip()
        city = self.request.GET.get("city", "").strip()
        industry = self.request.GET.get("industry", "").strip()
        if name:
            qs = qs.filter(name__icontains=name)
        if city:
            qs = qs.filter(city__icontains=city)
        if industry:
            qs = qs.filter(industry=industry)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        """Dodaje do kontekstu wartosci filtrow i dostepne branze."""
        ctx = super().get_context_data(**kwargs)
        ctx["filter_name"] = self.request.GET.get("name", "")
        ctx["filter_city"] = self.request.GET.get("city", "")
        ctx["filter_industry"] = self.request.GET.get("industry", "")
        ctx["industry_choices"] = Company.Industry.choices
        ctx["is_admin"] = _is_admin(self.request.user)
        return ctx


class CompanyDetailView(LoginRequiredMixin, DetailView):
    """Szczegolowy widok firmy z powiazanymi obiektami (N+1 safe)."""

    model = Company
    template_name = "companies/company_detail.html"
    context_object_name = "company"

    def get_queryset(self) -> QuerySet:
        """Ogranicza dostep: HANDLOWIEC widzi tylko swoje firmy."""
        qs = Company.objects.prefetch_related(
            "contacts",
            "leads",
            "tasks",
            "company_notes",
            "documents",
        ).select_related("owner")
        if not _is_admin(self.request.user):
            qs = qs.filter(owner=self.request.user)
        return qs

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = _is_admin(self.request.user)
        ctx["can_edit"] = _is_admin(self.request.user) or (
            self.object.owner == self.request.user
        )
        return ctx


_PREFILL_FIELDS = ("nip", "name", "address", "city", "postal_code")


class CompanyCreateView(LoginRequiredMixin, CreateView):
    """Widok tworzenia nowej firmy. Owner ustawiany automatycznie."""

    model = Company
    form_class = CompanyForm
    template_name = "companies/company_form.html"

    def get_initial(self) -> dict:
        """Wstępnie wypełnia formularz danymi z parametrów GET (po lookup NIP)."""
        initial = super().get_initial()
        for field in _PREFILL_FIELDS:
            val = self.request.GET.get(field, "").strip()
            if val:
                initial[field] = val
        return initial

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        logger.info(
            "Uzytkownik %s utworzyl firme: %s (id=%s)",
            self.request.user.username,
            self.object.name,
            self.object.pk,
        )
        messages.success(self.request, 'Firma "%s" zostala dodana.' % self.object.name)
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("companies:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Dodaj nowa firme"
        return ctx


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    """Widok edycji firmy. Tylko wlasciciel lub ADMIN."""

    model = Company
    form_class = CompanyForm
    template_name = "companies/company_form.html"

    def get_initial(self) -> dict:
        """Nadpisuje pola danymi z GET gdy użyto lookup NIP."""
        initial = super().get_initial()
        for field in _PREFILL_FIELDS:
            val = self.request.GET.get(field, "").strip()
            if val:
                initial[field] = val
        return initial

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user) and obj.owner != self.request.user:
            raise PermissionDenied(
                "Mozesz edytowac tylko firmy, ktorych jestes opiekunem."
            )
        return obj

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(
            "Uzytkownik %s zaktualizowal firme: %s (id=%s)",
            self.request.user.username,
            self.object.name,
            self.object.pk,
        )
        messages.success(
            self.request, 'Firma "%s" zostala zaktualizowana.' % self.object.name
        )
        return response

    def get_success_url(self) -> str:
        return reverse_lazy("companies:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs) -> dict:
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = "Edytuj: %s" % self.object.name
        return ctx


class NipLookupView(LoginRequiredMixin, View):
    """Pobiera dane firmy na podstawie NIP.

    Kolejność źródeł:
    1. CEIDG (dane.biznes.gov.pl) — gdy CEIDG_API_TOKEN ustawiony w .env
    2. Biała Lista MF (wl-api.mf.gov.pl) — fallback, bezpłatny, bez tokenu

    GET /companies/nip-lookup/?nip=XXXXXXXXXX
    Zwraca JSON: {name, address, city, postal_code, source} lub {error: "..."}
    """

    CEIDG_API_URL = "https://dane.biznes.gov.pl/api/ceidg/v2/firma?nip={nip}"
    MF_API_URL = "https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={date}"
    TIMEOUT = 5

    def get(self, request, *args, **kwargs):
        nip = request.GET.get("nip", "").strip().replace("-", "").replace(" ", "")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        next_url = request.GET.get("next", reverse("companies:create"))

        if not nip.isdigit() or len(nip) != 10:
            if is_ajax:
                return JsonResponse(
                    {"error": "Nieprawidłowy NIP (wymagane 10 cyfr)."}, status=400
                )
            messages.error(request, "Nieprawidłowy NIP — wpisz 10 cyfr.")
            return redirect(next_url)

        ceidg_token = getattr(settings, "CEIDG_API_TOKEN", "").strip()
        data = None
        if ceidg_token:
            data = self._lookup_ceidg(nip, ceidg_token)
            if data is not None:
                data["source"] = "CEIDG"
            else:
                logger.info("NipLookupView: CEIDG nie zwróciło danych, fallback na MF")

        if data is None:
            mf_response = self._lookup_mf(nip)
            if is_ajax:
                return mf_response
            # Dekoduj JsonResponse do słownika
            mf_data = json.loads(mf_response.content)
            if mf_response.status_code != 200:
                messages.error(request, mf_data.get("error", "Nie znaleziono firmy."))
                return redirect(next_url)
            data = mf_data

        if is_ajax:
            return JsonResponse(data)

        # Redirect z danymi jako parametry GET — CompanyCreateView.get_initial() je odbierze
        params = {"nip": nip}
        for field in ("name", "address", "city", "postal_code"):
            val = data.get(field, "")
            if val:
                params[field] = val
        return redirect(f"{next_url}?{urlencode(params)}")

    # ------------------------------------------------------------------
    # CEIDG
    # ------------------------------------------------------------------

    def _lookup_ceidg(self, nip: str, token: str) -> dict | None:
        """Odpytuje CEIDG API. Zwraca słownik danych lub None przy błędzie."""
        url = self.CEIDG_API_URL.format(nip=nip)
        try:
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning("NipLookupView CEIDG: błąd połączenia: %s", exc)
            return None

        if resp.status_code != 200:
            logger.warning(
                "NipLookupView CEIDG: status %s dla NIP %s", resp.status_code, nip
            )
            return None

        try:
            data = resp.json()
        except ValueError:
            logger.warning("NipLookupView CEIDG: błąd parsowania JSON")
            return None

        # CEIDG zwraca listę wpisów lub obiekt z kluczem "firma"/"wpisy"
        firms = (
            data if isinstance(data, list) else data.get("wpisy", data.get("firma", []))
        )
        if isinstance(firms, dict):
            firms = [firms]
        if not firms:
            return None

        firm = firms[0]
        name = firm.get("nazwa", "") or firm.get("imie", "") + " " + firm.get(
            "nazwisko", ""
        )
        adres = firm.get("adresDzialalnosci", firm.get("adresZamieszkania", {}))
        street = " ".join(
            filter(
                None,
                [
                    adres.get("ulica", ""),
                    adres.get("nrDomu", ""),
                    adres.get("nrLokalu", ""),
                ],
            )
        )
        if not street:
            street = adres.get("ulica", "")
        city = adres.get("miejscowosc", "")
        postal_code = adres.get("kodPocztowy", "")

        if not name and not city:
            return None

        return {
            "name": name.strip(),
            "address": street.strip(),
            "city": city,
            "postal_code": postal_code,
        }

    # ------------------------------------------------------------------
    # Biała Lista MF (fallback)
    # ------------------------------------------------------------------

    def _lookup_mf(self, nip: str):
        """Odpytuje Białą Listę MF i zwraca JsonResponse."""
        today = datetime.date.today().isoformat()
        url = self.MF_API_URL.format(nip=nip, date=today)
        try:
            resp = requests.get(url, timeout=self.TIMEOUT)
        except requests.Timeout:
            logger.warning("NipLookupView MF: timeout dla NIP %s", nip)
            return JsonResponse(
                {"error": "Serwis MF nie odpowiedział (timeout)."}, status=504
            )
        except requests.RequestException as exc:
            logger.error("NipLookupView MF: błąd połączenia dla NIP %s: %s", nip, exc)
            return JsonResponse({"error": "Błąd połączenia z serwisem MF."}, status=502)

        if resp.status_code == 400:
            return JsonResponse(
                {
                    "error": "Nieprawidłowy NIP — sprawdź poprawność numeru (suma kontrolna)."
                },
                status=400,
            )
        if resp.status_code == 404:
            return JsonResponse(
                {"error": "Nie znaleziono firmy o podanym NIP."}, status=404
            )
        if resp.status_code != 200:
            logger.warning(
                "NipLookupView MF: status %s dla NIP %s", resp.status_code, nip
            )
            return JsonResponse({"error": "Serwis MF zwrócił błąd."}, status=502)

        try:
            subject = resp.json().get("result", {}).get("subject", {})
        except ValueError:
            return JsonResponse({"error": "Błąd parsowania odpowiedzi MF."}, status=502)

        if not subject:
            return JsonResponse(
                {"error": "Nie znaleziono firmy o podanym NIP."}, status=404
            )

        name = subject.get("name", "")
        raw_address = subject.get("workingAddress", "") or subject.get(
            "residenceAddress", ""
        )
        city, postal_code, address = self._parse_mf_address(raw_address)

        return JsonResponse(
            {
                "name": name,
                "address": address,
                "city": city,
                "postal_code": postal_code,
                "source": "MF",
            }
        )

    @staticmethod
    def _parse_mf_address(raw: str) -> tuple[str, str, str]:
        """Parsuje adres MF w formacie 'ul. Przykładowa 1, 00-000 Miasto'.

        Returns:
            Krotka (city, postal_code, street_address).
        """
        if not raw:
            return "", "", ""
        parts = [p.strip() for p in raw.split(",")]
        street = parts[0] if parts else ""
        city = ""
        postal_code = ""
        for part in parts[1:]:
            tokens = part.strip().split(" ", 1)
            if len(tokens) == 2 and len(tokens[0]) == 6 and tokens[0][2] == "-":
                postal_code = tokens[0]
                city = tokens[1]
                break
            else:
                city = part.strip()
        return city, postal_code, street


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    """Widok usuwania firmy. Tylko ADMIN."""

    model = Company
    template_name = "companies/company_confirm_delete.html"
    success_url = reverse_lazy("companies:list")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not _is_admin(self.request.user):
            raise PermissionDenied(
                "Usuwanie firm jest zarezerwowane dla administratorow."
            )
        return obj

    def form_valid(self, form):
        company_name = self.object.name
        response = super().form_valid(form)
        logger.warning(
            "Uzytkownik %s usunał firme: %s",
            self.request.user.username,
            company_name,
        )
        messages.warning(self.request, 'Firma "%s" zostala usunieta.' % company_name)
        return response
