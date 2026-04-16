"""Testy widokow CRUD aplikacji notes."""

from __future__ import annotations

import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage
from apps.notes.models import Note

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


def _make_contact(first_name: str, last_name: str, company: Company) -> Contact:
    """Tworzy kontakt testowy."""
    return Contact.objects.create(
        first_name=first_name, last_name=last_name, company=company
    )


def _make_lead(title: str, company: Company, owner: User | None = None) -> Lead:
    """Tworzy lead testowy."""
    stage, _ = WorkflowStage.objects.get_or_create(
        order=1, defaults={"name": "Nowy", "color": "#6c757d"}
    )
    return Lead.objects.create(title=title, company=company, owner=owner, stage=stage)


def _make_deal(title: str, company: Company, owner: User | None = None) -> Deal:
    """Tworzy umowe testowa."""
    return Deal.objects.create(
        title=title,
        company=company,
        owner=owner,
        value="5000.00",
        close_date=datetime.date.today() + datetime.timedelta(days=30),
    )


def _make_note(
    content: str,
    author: User | None = None,
    company: Company | None = None,
) -> Note:
    """Tworzy notatke testowa."""
    return Note.objects.create(content=content, author=author, company=company)


# ---------------------------------------------------------------------------
# Testy: przekierowanie niezalogowanych
# ---------------------------------------------------------------------------


class NoteViewsAuthRedirectTest(TestCase):
    """Niezalogowani uzytkowniczy musza byc przekierowani na login."""

    def setUp(self) -> None:
        self.user = _make_user("auth_user")
        self.company = _make_company("Auth Co", owner=self.user)
        self.note = _make_note("Tresc notatki", author=self.user, company=self.company)

    def _assert_redirects_to_login(self, url: str, method: str = "get") -> None:
        response = getattr(self.client, method)(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_list_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("notes:list"))

    def test_detail_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("notes:detail", kwargs={"pk": self.note.pk})
        )

    def test_create_requires_login(self) -> None:
        self._assert_redirects_to_login(reverse("notes:create"))

    def test_update_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("notes:update", kwargs={"pk": self.note.pk})
        )

    def test_delete_requires_login(self) -> None:
        self._assert_redirects_to_login(
            reverse("notes:delete", kwargs={"pk": self.note.pk})
        )


# ---------------------------------------------------------------------------
# Testy: NoteListView
# ---------------------------------------------------------------------------


class NoteListViewTest(TestCase):
    """Testy widoku listy notatek."""

    def setUp(self) -> None:
        self.admin = _make_user("list_admin", role=UserProfile.Role.ADMIN)
        self.author = _make_user("list_author")
        self.other = _make_user("list_other")
        self.company = _make_company("List Co", owner=self.author)
        self.own_note = _make_note(
            "Moja notatka", author=self.author, company=self.company
        )
        self.other_note = _make_note("Cudza notatka", author=self.other)

    def test_list_returns_200(self) -> None:
        self.client.force_login(self.author)
        response = self.client.get(reverse("notes:list"))
        self.assertEqual(response.status_code, 200)

    def test_admin_sees_all_notes(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("notes:list"))
        notes = list(response.context["notes"])
        self.assertIn(self.own_note, notes)
        self.assertIn(self.other_note, notes)

    def test_handlowiec_sees_only_own_notes(self) -> None:
        self.client.force_login(self.author)
        response = self.client.get(reverse("notes:list"))
        notes = list(response.context["notes"])
        self.assertIn(self.own_note, notes)
        self.assertNotIn(self.other_note, notes)

    def test_filter_by_company_name(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("notes:list"), {"company": "List Co"})
        notes = list(response.context["notes"])
        self.assertIn(self.own_note, notes)
        self.assertNotIn(self.other_note, notes)

    def test_context_has_is_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("notes:list"))
        self.assertTrue(response.context["is_admin"])


# ---------------------------------------------------------------------------
# Testy: NoteDetailView
# ---------------------------------------------------------------------------


class NoteDetailViewTest(TestCase):
    """Testy widoku szczegolowego notatki."""

    def setUp(self) -> None:
        self.author = _make_user("detail_author")
        self.other = _make_user("detail_other")
        self.admin = _make_user("detail_admin", role=UserProfile.Role.ADMIN)
        self.company = _make_company("Detail Co", owner=self.author)
        self.note = _make_note(
            "Szczegolowa notatka", author=self.author, company=self.company
        )

    def test_author_can_view_note(self) -> None:
        self.client.force_login(self.author)
        response = self.client.get(reverse("notes:detail", kwargs={"pk": self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_any_note(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("notes:detail", kwargs={"pk": self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_404(self) -> None:
        self.client.force_login(self.other)
        response = self.client.get(reverse("notes:detail", kwargs={"pk": self.note.pk}))
        self.assertEqual(response.status_code, 404)

    def test_context_has_can_edit_true_for_author(self) -> None:
        self.client.force_login(self.author)
        response = self.client.get(reverse("notes:detail", kwargs={"pk": self.note.pk}))
        self.assertTrue(response.context["can_edit"])

    def test_context_has_is_admin_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("notes:detail", kwargs={"pk": self.note.pk}))
        self.assertTrue(response.context["is_admin"])


# ---------------------------------------------------------------------------
# Testy: NoteCreateView
# ---------------------------------------------------------------------------


class NoteCreateViewTest(TestCase):
    """Testy widoku tworzenia notatki."""

    def setUp(self) -> None:
        self.user = _make_user("create_user")
        self.company = _make_company("Create Co", owner=self.user)

    def test_create_get_returns_200(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("notes:create"))
        self.assertEqual(response.status_code, 200)

    def test_create_note_success(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("notes:create"),
            {"content": "Nowa notatka testowa"},
        )
        self.assertEqual(Note.objects.filter(content="Nowa notatka testowa").count(), 1)
        note = Note.objects.get(content="Nowa notatka testowa")
        self.assertRedirects(response, reverse("notes:detail", kwargs={"pk": note.pk}))

    def test_create_sets_author(self) -> None:
        self.client.force_login(self.user)
        self.client.post(
            reverse("notes:create"),
            {"content": "Notatka z autorem"},
        )
        note = Note.objects.get(content="Notatka z autorem")
        self.assertEqual(note.author, self.user)

    def test_create_prefill_company_id(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("notes:create"), {"company_id": self.company.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("company"), self.company)

    def test_create_prefill_lead_id(self) -> None:
        lead = _make_lead("Test lead", self.company, owner=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notes:create"), {"lead_id": lead.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("lead"), lead)

    def test_create_prefill_deal_id(self) -> None:
        deal = _make_deal("Test deal", self.company, owner=self.user)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notes:create"), {"deal_id": deal.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("deal"), deal)

    def test_create_prefill_contact_id(self) -> None:
        contact = _make_contact("Jan", "Kowalski", self.company)
        self.client.force_login(self.user)
        response = self.client.get(reverse("notes:create"), {"contact_id": contact.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("contact"), contact)


# ---------------------------------------------------------------------------
# Testy: NoteUpdateView
# ---------------------------------------------------------------------------


class NoteUpdateViewTest(TestCase):
    """Testy widoku edycji notatki."""

    def setUp(self) -> None:
        self.author = _make_user("update_author")
        self.other = _make_user("update_other")
        self.admin = _make_user("update_admin", role=UserProfile.Role.ADMIN)
        self.company = _make_company("Update Co", owner=self.author)
        self.note = _make_note(
            "Notatka do edycji", author=self.author, company=self.company
        )

    def test_author_can_edit(self) -> None:
        self.client.force_login(self.author)
        response = self.client.get(reverse("notes:update", kwargs={"pk": self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_edit_any_note(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("notes:update", kwargs={"pk": self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_403(self) -> None:
        self.client.force_login(self.other)
        response = self.client.get(reverse("notes:update", kwargs={"pk": self.note.pk}))
        self.assertEqual(response.status_code, 403)

    def test_update_note_success(self) -> None:
        self.client.force_login(self.author)
        response = self.client.post(
            reverse("notes:update", kwargs={"pk": self.note.pk}),
            {"content": "Zaktualizowana notatka"},
        )
        self.note.refresh_from_db()
        self.assertEqual(self.note.content, "Zaktualizowana notatka")
        self.assertRedirects(
            response, reverse("notes:detail", kwargs={"pk": self.note.pk})
        )


# ---------------------------------------------------------------------------
# Testy: NoteDeleteView
# ---------------------------------------------------------------------------


class NoteDeleteViewTest(TestCase):
    """Testy widoku usuwania notatki (autor lub ADMIN)."""

    def setUp(self) -> None:
        self.author = _make_user("delete_author")
        self.other = _make_user("delete_other")
        self.admin = _make_user("delete_admin", role=UserProfile.Role.ADMIN)
        self.company = _make_company("Delete Co", owner=self.author)

    def _fresh_note(self) -> Note:
        return _make_note("Notatka do usuniecia", author=self.author)

    def test_author_can_delete_own_note(self) -> None:
        note = self._fresh_note()
        self.client.force_login(self.author)
        response = self.client.post(reverse("notes:delete", kwargs={"pk": note.pk}))
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())
        self.assertRedirects(response, reverse("notes:list"))

    def test_admin_can_delete_any_note(self) -> None:
        note = self._fresh_note()
        self.client.force_login(self.admin)
        response = self.client.post(reverse("notes:delete", kwargs={"pk": note.pk}))
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())
        self.assertRedirects(response, reverse("notes:list"))

    def test_other_handlowiec_gets_403_on_delete(self) -> None:
        note = self._fresh_note()
        self.client.force_login(self.other)
        response = self.client.post(reverse("notes:delete", kwargs={"pk": note.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Note.objects.filter(pk=note.pk).exists())

    def test_delete_confirm_page_returns_200_for_author(self) -> None:
        note = self._fresh_note()
        self.client.force_login(self.author)
        response = self.client.get(reverse("notes:delete", kwargs={"pk": note.pk}))
        self.assertEqual(response.status_code, 200)
