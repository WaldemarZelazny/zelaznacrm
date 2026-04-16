"""Testy modelu UserProfile i sygnału auto-tworzenia profilu."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.models import UserProfile


class UserProfileStrTest(TestCase):
    """Testy metody __str__ i właściwości modelu UserProfile."""

    def setUp(self) -> None:
        """Tworzy użytkownika – sygnał automatycznie tworzy profil."""
        self.user = User.objects.create_user(
            username="jan.kowalski",
            first_name="Jan",
            last_name="Kowalski",
            password="testpass123",
        )
        # Sygnał post_save stworzył profil automatycznie – pobieramy go
        # i uzupełniamy pola potrzebne do testów.
        self.profile = self.user.profile
        self.profile.role = UserProfile.Role.HANDLOWIEC
        self.profile.phone = "600 100 200"
        self.profile.save()

    def test_str_returns_full_name_and_role(self) -> None:
        """__str__ powinien zwracać imię, nazwisko i rolę po polsku."""
        self.assertEqual(str(self.profile), "Jan Kowalski (Handlowiec)")

    def test_str_falls_back_to_username(self) -> None:
        """__str__ używa username gdy brak imienia i nazwiska."""
        user_no_name = User.objects.create_user(username="noname")
        profile = user_no_name.profile
        profile.role = UserProfile.Role.ADMIN
        profile.save()
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
        """Nowo utworzony profil (przez sygnał) domyślnie ma rolę HANDLOWIEC."""
        user = User.objects.create_user(username="test_default")
        # Sygnał już stworzył profil – sprawdzamy jego domyślną rolę.
        self.assertEqual(user.profile.role, UserProfile.Role.HANDLOWIEC)

    def test_role_choices_contain_admin_and_handlowiec(self) -> None:
        """TextChoices zawiera dokładnie dwie role: ADMIN i HANDLOWIEC."""
        values = [choice.value for choice in UserProfile.Role]
        self.assertIn("ADMIN", values)
        self.assertIn("HANDLOWIEC", values)
        self.assertEqual(len(values), 2)

    def test_cascade_delete_removes_profile(self) -> None:
        """Usunięcie User kasuje powiązany UserProfile (CASCADE)."""
        user = User.objects.create_user(username="to_delete")
        profile_id = user.profile.pk
        user.delete()
        self.assertFalse(UserProfile.objects.filter(pk=profile_id).exists())

    def test_phone_optional(self) -> None:
        """Pole phone jest opcjonalne (blank=True) – domyślnie puste."""
        user = User.objects.create_user(username="no_phone")
        self.assertEqual(user.profile.phone, "")


class UserProfileSignalTest(TestCase):
    """Testy sygnału post_save automatycznie tworzącego UserProfile."""

    def test_profile_created_automatically_on_user_create(self) -> None:
        """Sygnał tworzy UserProfile automatycznie przy create_user."""
        user = User.objects.create_user(username="signal_test")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_accessible_via_reverse_relation(self) -> None:
        """Profil jest dostępny przez user.profile po auto-utworzeniu."""
        user = User.objects.create_user(username="reverse_rel")
        self.assertIsInstance(user.profile, UserProfile)

    def test_only_one_profile_created_per_user(self) -> None:
        """Dla jednego User powstaje dokładnie jeden profil."""
        user = User.objects.create_user(username="one_profile")
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_profile_not_created_on_user_update(self) -> None:
        """Sygnał NIE tworzy drugiego profilu przy zapisie istniejącego User."""
        user = User.objects.create_user(username="update_test")
        # Aktualizujemy User – sygnał uruchomi się, ale created=False.
        user.first_name = "Zmienione"
        user.save()
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_auto_profile_has_default_role_handlowiec(self) -> None:
        """Automatycznie utworzony profil ma domyślną rolę HANDLOWIEC."""
        user = User.objects.create_user(username="role_check")
        self.assertEqual(user.profile.role, UserProfile.Role.HANDLOWIEC)

    def test_profile_created_for_superuser(self) -> None:
        """Sygnał działa też dla create_superuser."""
        admin = User.objects.create_superuser(
            username="superadmin",
            email="sa@test.pl",
            password="adminpass",
        )
        self.assertTrue(UserProfile.objects.filter(user=admin).exists())
