"""Testy widokow CRUD aplikacji companies."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.companies.models import Company

# ---------------------------------------------------------------------------
# Pomocnicze funkcje
# ---------------------------------------------------------------------------


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    """Tworzy uzytkownika z profilem o podanej roli."""
    user = User.objects.create_user(username=username, password="testpass")
    user.profile.role = role
    user.profile.save()
    return user


def _make_company(name: str, owner: User | None = None) -> Company:
    """Tworzy firme testowa."""
    return Company.objects.create(name=name, owner=owner)


# ---------------------------------------------------------------------------
# Testy: przekierowanie niezalogowanych
# ---------------------------------------------------------------------------


class CompanyViewsAuthRedirectTest(TestCase):
    """Niezalogowani uzytkowniczy musza byc przekierowani na login."""

    def setUp(self) -> None:
        self.company = _make_company("Acme SA")

    def _assert_redirects_to_login(self, url: str, method: str = "get") -> None:
        response = getattr(self.client, method)(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_list_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("companies:list"))

    def test_detail_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("companies:detail", kwargs={"pk": self.company.pk})
        )

    def test_create_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("companies:create"))

    def test_update_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("companies:update", kwargs={"pk": self.company.pk})
        )

    def test_delete_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("companies:delete", kwargs={"pk": self.company.pk})
        )


# ---------------------------------------------------------------------------
# Testy: CompanyListView
# ---------------------------------------------------------------------------


class CompanyListViewTest(TestCase):
    """Testy widoku listy firm."""

    def setUp(self) -> None:
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec1")
        self.other = _make_user("handlowiec2")
        self.own_company = _make_company("Moja Firma", owner=self.handlowiec)
        self.other_company = _make_company("Cudznia Firma", owner=self.other)

    def test_handlowiec_sees_only_own_companies(self) -> None:
        """HANDLOWIEC widzi tylko swoje firmy."""
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("companies:list"))
        self.assertEqual(response.status_code, 200)
        companies = list(response.context["companies"])
        self.assertIn(self.own_company, companies)
        self.assertNotIn(self.other_company, companies)

    def test_admin_sees_all_companies(self) -> None:
        """ADMIN widzi wszystkie firmy."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("companies:list"))
        self.assertEqual(response.status_code, 200)
        companies = list(response.context["companies"])
        self.assertIn(self.own_company, companies)
        self.assertIn(self.other_company, companies)

    def test_filter_by_name(self) -> None:
        """Filtr name zaweza wyniki do pasujacych nazw."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("companies:list"), {"name": "Moja"})
        companies = list(response.context["companies"])
        self.assertIn(self.own_company, companies)
        self.assertNotIn(self.other_company, companies)

    def test_filter_by_city(self) -> None:
        """Filtr city zaweza wyniki do podanego miasta."""
        Company.objects.create(name="Warszawa Corp", city="Warszawa")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("companies:list"), {"city": "Warszawa"})
        names = [c.name for c in response.context["companies"]]
        self.assertIn("Warszawa Corp", names)
        self.assertNotIn("Moja Firma", names)

    def test_filter_by_industry(self) -> None:
        """Filtr industry zaweza wyniki do podanej branzy."""
        Company.objects.create(name="Tech Co", industry=Company.Industry.IT)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("companies:list"), {"industry": "IT"})
        names = [c.name for c in response.context["companies"]]
        self.assertIn("Tech Co", names)

    def test_uses_correct_template(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("companies:list"))
        self.assertTemplateUsed(response, "companies/company_list.html")

    def test_context_contains_industry_choices(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("companies:list"))
        self.assertIn("industry_choices", response.context)


# ---------------------------------------------------------------------------
# Testy: CompanyDetailView
# ---------------------------------------------------------------------------


class CompanyDetailViewTest(TestCase):
    """Testy widoku szczegolowego firmy."""

    def setUp(self) -> None:
        self.owner = _make_user("owner_user")
        self.other = _make_user("other_user")
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.company = _make_company("Test SA", owner=self.owner)

    def test_owner_can_view_own_company(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("companies:detail", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["company"], self.company)

    def test_admin_can_view_any_company(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("companies:detail", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_handlowiec_cannot_view_other_company(self) -> None:
        """Handlowiec nie widzi cudzej firmy - dostaje 404."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("companies:detail", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_uses_correct_template(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("companies:detail", kwargs={"pk": self.company.pk})
        )
        self.assertTemplateUsed(response, "companies/company_detail.html")

    def test_context_can_edit_true_for_owner(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("companies:detail", kwargs={"pk": self.company.pk})
        )
        self.assertTrue(response.context["can_edit"])

    def test_context_can_edit_true_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("companies:detail", kwargs={"pk": self.company.pk})
        )
        self.assertTrue(response.context["can_edit"])


# ---------------------------------------------------------------------------
# Testy: CompanyCreateView
# ---------------------------------------------------------------------------


class CompanyCreateViewTest(TestCase):
    """Testy widoku tworzenia firmy."""

    def setUp(self) -> None:
        self.user = _make_user("creator")

    def test_get_returns_200(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("companies:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "companies/company_form.html")

    def test_post_creates_company_and_sets_owner(self) -> None:
        """POST z poprawnymi danymi tworzy firme i ustawia owner."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("companies:create"),
            data={"name": "Nowa Firma Sp. z o.o.", "industry": "IT", "is_active": True},
        )
        self.assertEqual(Company.objects.count(), 1)
        company = Company.objects.first()
        self.assertEqual(company.owner, self.user)
        self.assertRedirects(
            response,
            reverse("companies:detail", kwargs={"pk": company.pk}),
        )

    def test_post_invalid_data_shows_form_again(self) -> None:
        """POST z brakujaca nazwa zwraca formularz z bledami."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("companies:create"),
            data={"name": "", "industry": "IT"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Company.objects.count(), 0)


# ---------------------------------------------------------------------------
# Testy: CompanyUpdateView
# ---------------------------------------------------------------------------


class CompanyUpdateViewTest(TestCase):
    """Testy widoku edycji firmy."""

    def setUp(self) -> None:
        self.owner = _make_user("owner_user")
        self.other = _make_user("other_user")
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.company = _make_company("Stara Nazwa", owner=self.owner)

    def test_owner_can_edit(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("companies:update", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_edit_any_company(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("companies:update", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_403(self) -> None:
        """Inny handlowiec probujacy edytowac cudzą firme dostaje 403."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("companies:update", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_post_updates_company_name(self) -> None:
        """POST z poprawnymi danymi aktualizuje firme."""
        self.client.force_login(self.owner)
        self.client.post(
            reverse("companies:update", kwargs={"pk": self.company.pk}),
            data={"name": "Nowa Nazwa SA", "industry": "IT", "is_active": True},
        )
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, "Nowa Nazwa SA")


# ---------------------------------------------------------------------------
# Testy: CompanyDeleteView
# ---------------------------------------------------------------------------


class CompanyDeleteViewTest(TestCase):
    """Testy widoku usuwania firmy (tylko ADMIN)."""

    def setUp(self) -> None:
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec_user")
        self.company = _make_company("Do Usuniecia", owner=self.admin)

    def test_handlowiec_gets_403_on_delete_get(self) -> None:
        """Handlowiec nie moze wejsc na strone usuwania firmy."""
        self.client.force_login(self.handlowiec)
        response = self.client.get(
            reverse("companies:delete", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_delete_confirmation(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("companies:delete", kwargs={"pk": self.company.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "companies/company_confirm_delete.html")

    def test_admin_can_delete_company(self) -> None:
        """ADMIN moze usunac firme przez POST."""
        self.client.force_login(self.admin)
        self.client.post(reverse("companies:delete", kwargs={"pk": self.company.pk}))
        self.assertFalse(Company.objects.filter(pk=self.company.pk).exists())

    def test_delete_redirects_to_list(self) -> None:
        """Po usunieciu nastepuje przekierowanie na liste firm."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("companies:delete", kwargs={"pk": self.company.pk})
        )
        self.assertRedirects(response, reverse("companies:list"))

    def test_handlowiec_cannot_delete_via_post(self) -> None:
        """Handlowiec nie moze usunac firmy nawet przez POST."""
        self.client.force_login(self.handlowiec)
        self.client.post(reverse("companies:delete", kwargs={"pk": self.company.pk}))
        # Firma powinna nadal istniesc
        self.assertTrue(Company.objects.filter(pk=self.company.pk).exists())
