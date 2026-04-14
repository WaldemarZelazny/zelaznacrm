"""Testy widokow CRUD aplikacji contacts."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.contacts.models import Contact

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


def _make_contact(
    first_name: str,
    last_name: str,
    company: Company,
    owner: User | None = None,
) -> Contact:
    """Tworzy kontakt testowy."""
    return Contact.objects.create(
        first_name=first_name,
        last_name=last_name,
        company=company,
        owner=owner,
    )


# ---------------------------------------------------------------------------
# Testy: przekierowanie niezalogowanych
# ---------------------------------------------------------------------------


class ContactViewsAuthRedirectTest(TestCase):
    """Niezalogowani uzytkowniczy musza byc przekierowani na login."""

    def setUp(self) -> None:
        self.owner = _make_user("owner_user")
        self.company = _make_company("Acme SA", owner=self.owner)
        self.contact = _make_contact("Jan", "Kowalski", self.company, owner=self.owner)

    def _assert_redirects_to_login(self, url: str, method: str = "get") -> None:
        response = getattr(self.client, method)(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_list_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("contacts:list"))

    def test_detail_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("contacts:detail", kwargs={"pk": self.contact.pk})
        )

    def test_create_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("contacts:create"))

    def test_update_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("contacts:update", kwargs={"pk": self.contact.pk})
        )

    def test_delete_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("contacts:delete", kwargs={"pk": self.contact.pk})
        )


# ---------------------------------------------------------------------------
# Testy: ContactListView
# ---------------------------------------------------------------------------


class ContactListViewTest(TestCase):
    """Testy widoku listy kontaktow."""

    def setUp(self) -> None:
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec1")
        self.other = _make_user("handlowiec2")
        self.company = _make_company("Firma A", owner=self.handlowiec)
        self.other_company = _make_company("Firma B", owner=self.other)
        self.own_contact = _make_contact(
            "Jan", "Kowalski", self.company, owner=self.handlowiec
        )
        self.other_contact = _make_contact(
            "Anna", "Nowak", self.other_company, owner=self.other
        )

    def test_handlowiec_sees_only_own_contacts(self) -> None:
        """HANDLOWIEC widzi tylko swoje kontakty."""
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("contacts:list"))
        self.assertEqual(response.status_code, 200)
        contacts = list(response.context["contacts"])
        self.assertIn(self.own_contact, contacts)
        self.assertNotIn(self.other_contact, contacts)

    def test_admin_sees_all_contacts(self) -> None:
        """ADMIN widzi wszystkie kontakty."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("contacts:list"))
        self.assertEqual(response.status_code, 200)
        contacts = list(response.context["contacts"])
        self.assertIn(self.own_contact, contacts)
        self.assertIn(self.other_contact, contacts)

    def test_filter_by_name(self) -> None:
        """Filtr name zaweza wyniki do pasujacych nazwisk."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("contacts:list"), {"name": "Kowalski"})
        contacts = list(response.context["contacts"])
        self.assertIn(self.own_contact, contacts)
        self.assertNotIn(self.other_contact, contacts)

    def test_filter_by_company(self) -> None:
        """Filtr company zaweza wyniki do podanej firmy."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse("contacts:list"), {"company": "Firma A"})
        contacts = list(response.context["contacts"])
        self.assertIn(self.own_contact, contacts)
        self.assertNotIn(self.other_contact, contacts)

    def test_filter_by_department(self) -> None:
        """Filtr department zaweza wyniki do podanego dzialu."""
        Contact.objects.create(
            first_name="Piotr",
            last_name="IT",
            company=self.company,
            department=Contact.Department.IT,
            owner=self.admin,
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("contacts:list"), {"department": "IT"})
        names = [c.last_name for c in response.context["contacts"]]
        self.assertIn("IT", names)
        self.assertNotIn("Kowalski", names)

    def test_uses_correct_template(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("contacts:list"))
        self.assertTemplateUsed(response, "contacts/contact_list.html")

    def test_context_contains_department_choices(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("contacts:list"))
        self.assertIn("department_choices", response.context)


# ---------------------------------------------------------------------------
# Testy: ContactDetailView
# ---------------------------------------------------------------------------


class ContactDetailViewTest(TestCase):
    """Testy widoku szczegolowego kontaktu."""

    def setUp(self) -> None:
        self.owner = _make_user("owner_user")
        self.other = _make_user("other_user")
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.company = _make_company("Test SA", owner=self.owner)
        self.contact = _make_contact("Jan", "Kowalski", self.company, owner=self.owner)

    def test_owner_can_view_own_contact(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("contacts:detail", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["contact"], self.contact)

    def test_admin_can_view_any_contact(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("contacts:detail", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_handlowiec_cannot_view_other_contact(self) -> None:
        """Handlowiec nie widzi cudzego kontaktu - dostaje 404."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("contacts:detail", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_uses_correct_template(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("contacts:detail", kwargs={"pk": self.contact.pk})
        )
        self.assertTemplateUsed(response, "contacts/contact_detail.html")

    def test_context_can_edit_true_for_owner(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("contacts:detail", kwargs={"pk": self.contact.pk})
        )
        self.assertTrue(response.context["can_edit"])

    def test_context_can_edit_true_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("contacts:detail", kwargs={"pk": self.contact.pk})
        )
        self.assertTrue(response.context["can_edit"])


# ---------------------------------------------------------------------------
# Testy: ContactCreateView
# ---------------------------------------------------------------------------


class ContactCreateViewTest(TestCase):
    """Testy widoku tworzenia kontaktu."""

    def setUp(self) -> None:
        self.user = _make_user("creator")
        self.company = _make_company("Moja Firma", owner=self.user)

    def test_get_returns_200(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("contacts:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contacts/contact_form.html")

    def test_post_creates_contact_and_sets_owner(self) -> None:
        """POST z poprawnymi danymi tworzy kontakt i ustawia owner."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("contacts:create"),
            data={
                "first_name": "Jan",
                "last_name": "Nowak",
                "company": self.company.pk,
                "department": Contact.Department.IT,
                "is_active": True,
            },
        )
        self.assertEqual(Contact.objects.count(), 1)
        contact = Contact.objects.first()
        self.assertEqual(contact.owner, self.user)
        self.assertRedirects(
            response,
            reverse("contacts:detail", kwargs={"pk": contact.pk}),
        )

    def test_post_invalid_data_shows_form_again(self) -> None:
        """POST z brakujaca firma zwraca formularz z bledami."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("contacts:create"),
            data={"first_name": "Jan", "last_name": "Nowak", "company": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Contact.objects.count(), 0)

    def test_get_with_company_id_prefills_company(self) -> None:
        """GET z ?company_id= wstepnie wypelnia pole company."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("contacts:create"), {"company_id": self.company.pk}
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.initial.get("company"), self.company)

    def test_handlowiec_company_queryset_limited_to_own(self) -> None:
        """Formularz dla HANDLOWCA zawiera tylko jego firmy."""
        other = _make_user("other_user")
        _make_company("Cudza Firma", owner=other)
        self.client.force_login(self.user)
        response = self.client.get(reverse("contacts:create"))
        form = response.context["form"]
        companies = list(form.fields["company"].queryset)
        self.assertIn(self.company, companies)
        for c in companies:
            self.assertNotEqual(c.name, "Cudza Firma")

    def test_admin_company_queryset_contains_all(self) -> None:
        """Formularz dla ADMINA zawiera wszystkie firmy."""
        admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        other = _make_user("other_user")
        other_company = _make_company("Cudza Firma", owner=other)
        self.client.force_login(admin)
        response = self.client.get(reverse("contacts:create"))
        form = response.context["form"]
        companies = list(form.fields["company"].queryset)
        self.assertIn(self.company, companies)
        self.assertIn(other_company, companies)


# ---------------------------------------------------------------------------
# Testy: ContactUpdateView
# ---------------------------------------------------------------------------


class ContactUpdateViewTest(TestCase):
    """Testy widoku edycji kontaktu."""

    def setUp(self) -> None:
        self.owner = _make_user("owner_user")
        self.other = _make_user("other_user")
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.company = _make_company("Stara Firma", owner=self.owner)
        self.contact = _make_contact("Jan", "Kowalski", self.company, owner=self.owner)

    def test_owner_can_edit(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("contacts:update", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_edit_any_contact(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("contacts:update", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_403(self) -> None:
        """Inny handlowiec probujacy edytowac cudzy kontakt dostaje 403."""
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("contacts:update", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_post_updates_contact_last_name(self) -> None:
        """POST z poprawnymi danymi aktualizuje kontakt."""
        self.client.force_login(self.owner)
        self.client.post(
            reverse("contacts:update", kwargs={"pk": self.contact.pk}),
            data={
                "first_name": "Jan",
                "last_name": "Zmieniony",
                "company": self.company.pk,
                "department": Contact.Department.IT,
                "is_active": True,
            },
        )
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.last_name, "Zmieniony")


# ---------------------------------------------------------------------------
# Testy: ContactDeleteView
# ---------------------------------------------------------------------------


class ContactDeleteViewTest(TestCase):
    """Testy widoku usuwania kontaktu (tylko ADMIN)."""

    def setUp(self) -> None:
        self.admin = _make_user("admin_user", UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("handlowiec_user")
        self.company = _make_company("Firma testowa", owner=self.admin)
        self.contact = _make_contact("Do", "Usuniecia", self.company, owner=self.admin)

    def test_handlowiec_gets_403_on_delete_get(self) -> None:
        """Handlowiec nie moze wejsc na strone usuwania kontaktu."""
        self.client.force_login(self.handlowiec)
        response = self.client.get(
            reverse("contacts:delete", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_delete_confirmation(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("contacts:delete", kwargs={"pk": self.contact.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "contacts/contact_confirm_delete.html")

    def test_admin_can_delete_contact(self) -> None:
        """ADMIN moze usunac kontakt przez POST."""
        self.client.force_login(self.admin)
        self.client.post(reverse("contacts:delete", kwargs={"pk": self.contact.pk}))
        self.assertFalse(Contact.objects.filter(pk=self.contact.pk).exists())

    def test_delete_redirects_to_list(self) -> None:
        """Po usunieciu nastepuje przekierowanie na liste kontaktow."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("contacts:delete", kwargs={"pk": self.contact.pk})
        )
        self.assertRedirects(response, reverse("contacts:list"))

    def test_handlowiec_cannot_delete_via_post(self) -> None:
        """Handlowiec nie moze usunac kontaktu nawet przez POST."""
        self.client.force_login(self.handlowiec)
        self.client.post(reverse("contacts:delete", kwargs={"pk": self.contact.pk}))
        # Kontakt powinien nadal istniec
        self.assertTrue(Contact.objects.filter(pk=self.contact.pk).exists())
