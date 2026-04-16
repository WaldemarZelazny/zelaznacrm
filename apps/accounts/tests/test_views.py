"""Testy widokow zarzadzania uzytkownikami (accounts)."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile

# ---------------------------------------------------------------------------
# Pomocnicze funkcje
# ---------------------------------------------------------------------------


def _make_user(
    username: str,
    role: str = UserProfile.Role.HANDLOWIEC,
    first_name: str = "",
    last_name: str = "",
    email: str = "",
) -> User:
    user = User.objects.create_user(
        username=username,
        password="testpass",
        first_name=first_name,
        last_name=last_name,
        email=email,
    )
    user.profile.role = role
    user.profile.save()
    return user


# ---------------------------------------------------------------------------
# Testy: UserListView
# ---------------------------------------------------------------------------


class UserListViewTest(TestCase):
    """Testy listy uzytkownikow (tylko ADMIN)."""

    def setUp(self) -> None:
        self.admin = _make_user("ul_admin", role=UserProfile.Role.ADMIN)
        self.hw1 = _make_user("ul_hw1")
        self.hw2 = _make_user("ul_hw2")

    def test_list_requires_login(self) -> None:
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_list_403_for_handlowiec(self) -> None:
        self.client.force_login(self.hw1)
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_list_returns_200_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_all_users(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:user_list"))
        users = list(response.context["users"])
        self.assertIn(self.hw1, users)
        self.assertIn(self.hw2, users)
        self.assertIn(self.admin, users)

    def test_list_context_has_is_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:user_list"))
        self.assertTrue(response.context["is_admin"])


# ---------------------------------------------------------------------------
# Testy: UserDetailView
# ---------------------------------------------------------------------------


class UserDetailViewTest(TestCase):
    """Testy widoku szczegolowego profilu uzytkownika."""

    def setUp(self) -> None:
        self.admin = _make_user("ud_admin", role=UserProfile.Role.ADMIN)
        self.hw = _make_user("ud_hw", first_name="Jan", last_name="Kowalski")
        self.other = _make_user("ud_other")

    def test_detail_requires_login(self) -> None:
        response = self.client.get(
            reverse("accounts:user_detail", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_owner_can_view_own_profile(self) -> None:
        self.client.force_login(self.hw)
        response = self.client.get(
            reverse("accounts:user_detail", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_any_profile(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("accounts:user_detail", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_403(self) -> None:
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("accounts:user_detail", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_context_has_can_edit_true_for_owner(self) -> None:
        self.client.force_login(self.hw)
        response = self.client.get(
            reverse("accounts:user_detail", kwargs={"pk": self.hw.pk})
        )
        self.assertTrue(response.context["can_edit"])

    def test_context_has_is_admin_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("accounts:user_detail", kwargs={"pk": self.hw.pk})
        )
        self.assertTrue(response.context["is_admin"])


# ---------------------------------------------------------------------------
# Testy: UserCreateView
# ---------------------------------------------------------------------------


class UserCreateViewTest(TestCase):
    """Testy widoku tworzenia uzytkownika (tylko ADMIN)."""

    def setUp(self) -> None:
        self.admin = _make_user("uc_admin", role=UserProfile.Role.ADMIN)
        self.hw = _make_user("uc_hw")

    def test_create_requires_login(self) -> None:
        response = self.client.get(reverse("accounts:user_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_create_403_for_handlowiec(self) -> None:
        self.client.force_login(self.hw)
        response = self.client.get(reverse("accounts:user_create"))
        self.assertEqual(response.status_code, 403)

    def test_create_get_returns_200_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:user_create"))
        self.assertEqual(response.status_code, 200)

    def test_create_user_success(self) -> None:
        self.client.force_login(self.admin)
        self.client.post(
            reverse("accounts:user_create"),
            {
                "username": "new_user",
                "first_name": "Anna",
                "last_name": "Nowak",
                "email": "anna@example.com",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": UserProfile.Role.HANDLOWIEC,
                "phone": "123456789",
            },
        )
        self.assertTrue(User.objects.filter(username="new_user").exists())

    def test_create_sets_profile_role(self) -> None:
        self.client.force_login(self.admin)
        self.client.post(
            reverse("accounts:user_create"),
            {
                "username": "role_user",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": UserProfile.Role.ADMIN,
                "phone": "",
            },
        )
        user = User.objects.get(username="role_user")
        self.assertEqual(user.profile.role, UserProfile.Role.ADMIN)

    def test_create_sets_profile_phone(self) -> None:
        self.client.force_login(self.admin)
        self.client.post(
            reverse("accounts:user_create"),
            {
                "username": "phone_user",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": UserProfile.Role.HANDLOWIEC,
                "phone": "987654321",
            },
        )
        user = User.objects.get(username="phone_user")
        self.assertEqual(user.profile.phone, "987654321")

    def test_create_redirects_to_detail(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("accounts:user_create"),
            {
                "username": "redirect_user",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
                "role": UserProfile.Role.HANDLOWIEC,
                "phone": "",
            },
        )
        user = User.objects.get(username="redirect_user")
        self.assertRedirects(
            response, reverse("accounts:user_detail", kwargs={"pk": user.pk})
        )


# ---------------------------------------------------------------------------
# Testy: UserUpdateView
# ---------------------------------------------------------------------------


class UserUpdateViewTest(TestCase):
    """Testy widoku edycji uzytkownika."""

    def setUp(self) -> None:
        self.admin = _make_user("uu_admin", role=UserProfile.Role.ADMIN)
        self.hw = _make_user("uu_hw", first_name="Piotr", last_name="Wisniak")
        self.other = _make_user("uu_other")

    def test_update_requires_login(self) -> None:
        response = self.client.get(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_owner_can_edit_own_profile(self) -> None:
        self.client.force_login(self.hw)
        response = self.client.get(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_edit_any_profile(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_other_handlowiec_gets_403(self) -> None:
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_update_changes_user_data(self) -> None:
        self.client.force_login(self.hw)
        self.client.post(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk}),
            {
                "first_name": "Nowe",
                "last_name": "Nazwisko",
                "email": "nowe@example.com",
                "phone": "111222333",
            },
        )
        self.hw.refresh_from_db()
        self.assertEqual(self.hw.first_name, "Nowe")
        self.assertEqual(self.hw.last_name, "Nazwisko")

    def test_update_changes_phone(self) -> None:
        self.client.force_login(self.hw)
        self.client.post(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk}),
            {
                "first_name": "Piotr",
                "last_name": "Wisniak",
                "email": "",
                "phone": "555666777",
            },
        )
        self.hw.profile.refresh_from_db()
        self.assertEqual(self.hw.profile.phone, "555666777")

    def test_admin_can_change_role(self) -> None:
        self.client.force_login(self.admin)
        self.client.post(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk}),
            {
                "first_name": "Piotr",
                "last_name": "Wisniak",
                "email": "",
                "role": UserProfile.Role.ADMIN,
                "phone": "",
            },
        )
        self.hw.profile.refresh_from_db()
        self.assertEqual(self.hw.profile.role, UserProfile.Role.ADMIN)

    def test_update_redirects_to_detail(self) -> None:
        self.client.force_login(self.hw)
        response = self.client.post(
            reverse("accounts:user_update", kwargs={"pk": self.hw.pk}),
            {
                "first_name": "Piotr",
                "last_name": "Wisniak",
                "email": "",
                "phone": "",
            },
        )
        self.assertRedirects(
            response,
            reverse("accounts:user_detail", kwargs={"pk": self.hw.pk}),
        )
