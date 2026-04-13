"""Testy modelu UserProfile aplikacji accounts."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import UserProfile


class UserProfileStrTest(TestCase):
    """Testy metody __str__ i właściwości modelu UserProfile."""

    def setUp(self) -> None:
        """Tworzy użytkownika testowego przed każdym testem."""
        self.user = User.objects.create_user(
            username="jan.kowalski",
            first_name="Jan",
            last_name="Kowalski",
            password="testpass123",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.HANDLOWIEC,
            phone="600 100 200",
        )

    def test_str_returns_full_name_and_role(self) -> None:
        """__str__ powinien zwracać imię, nazwisko i rolę po polsku."""
        self.assertEqual(str(self.profile), "Jan Kowalski (Handlowiec)")

    def test_str_falls_back_to_username(self) -> None:
        """__str__ używa username gdy brak imienia i nazwiska."""
        user_no_name = User.objects.create_user(username="noname")
        profile = UserProfile.objects.create(
            user=user_no_name,
            role=UserProfile.Role.ADMIN,
        )
        self.assertEqual(str(profile), "noname (Administrator)")

    def test_full_name_property(self) -> None:
        """Właściwość full_name zwraca pełne imię i nazwisko."""
        self.assertEqual(self.profile.full_name, "Jan Kowalski")

    def test_is_admin_false_for_handlowiec(self) -> None:
        """is_admin == False dla roli HANDLOWIEC."""
        self.assertFalse(self.profile.is_admin)

    def test_is_admin_true_for_admin_role(self) -> None:
        """is_admin == True dla roli ADMIN."""
        self.profile.role = UserProfile.Role.ADMIN
        self.assertTrue(self.profile.is_admin)


class UserProfileRoleTest(TestCase):
    """Testy pól i wartości domyślnych UserProfile."""

    def test_default_role_is_handlowiec(self) -> None:
        """Nowo utworzony profil domyślnie ma rolę HANDLOWIEC."""
        user = User.objects.create_user(username="test_default")
        profile = UserProfile.objects.create(user=user)
        self.assertEqual(profile.role, UserProfile.Role.HANDLOWIEC)

    def test_role_choices_contain_admin_and_handlowiec(self) -> None:
        """TextChoices zawiera dokładnie dwie role: ADMIN i HANDLOWIEC."""
        values = [choice.value for choice in UserProfile.Role]
        self.assertIn("ADMIN", values)
        self.assertIn("HANDLOWIEC", values)
        self.assertEqual(len(values), 2)

    def test_cascade_delete_removes_profile(self) -> None:
        """Usunięcie User kasuje powiązany UserProfile (CASCADE)."""
        user = User.objects.create_user(username="to_delete")
        profile_id = UserProfile.objects.create(user=user).pk
        user.delete()
        self.assertFalse(UserProfile.objects.filter(pk=profile_id).exists())

    def test_phone_optional(self) -> None:
        """Pole phone jest opcjonalne (blank=True)."""
        user = User.objects.create_user(username="no_phone")
        profile = UserProfile.objects.create(user=user)
        self.assertEqual(profile.phone, "")
