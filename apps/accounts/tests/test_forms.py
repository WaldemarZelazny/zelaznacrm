"""Testy formularzy aplikacji accounts."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.accounts.forms import UserCreateForm, UserUpdateForm
from apps.accounts.models import UserProfile


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    user = User.objects.create_user(username=username, password="pass")
    user.profile.role = role
    user.profile.save()
    return user


class UserCreateFormTest(TestCase):
    def _valid_data(self, **overrides) -> dict:
        data = {
            "username": "nowyuser",
            "first_name": "Jan",
            "last_name": "Kowalski",
            "email": "jan@example.com",
            "password1": "TrudneHaslo123!",
            "password2": "TrudneHaslo123!",
            "role": UserProfile.Role.HANDLOWIEC,
            "phone": "600100200",
        }
        data.update(overrides)
        return data

    def test_valid_data_is_valid(self):
        form = UserCreateForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_username_invalid(self):
        form = UserCreateForm(data=self._valid_data(username=""))
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_missing_password_invalid(self):
        form = UserCreateForm(data=self._valid_data(password1="", password2=""))
        self.assertFalse(form.is_valid())

    def test_password_mismatch_invalid(self):
        form = UserCreateForm(
            data=self._valid_data(password1="Abc123!", password2="Xyz789!")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_missing_role_invalid(self):
        form = UserCreateForm(data=self._valid_data(role=""))
        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)

    def test_phone_optional(self):
        form = UserCreateForm(data=self._valid_data(phone=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_admin_role_valid(self):
        form = UserCreateForm(data=self._valid_data(role=UserProfile.Role.ADMIN))
        self.assertTrue(form.is_valid(), form.errors)


class UserUpdateFormTest(TestCase):
    def setUp(self):
        self.user = _make_user("edytowany")

    def _valid_data(self, **overrides) -> dict:
        data = {
            "first_name": "Jan",
            "last_name": "Nowak",
            "email": "jan@example.com",
            "role": UserProfile.Role.HANDLOWIEC,
            "phone": "500600700",
        }
        data.update(overrides)
        return data

    def test_valid_data_admin_is_valid(self):
        form = UserUpdateForm(
            data=self._valid_data(), instance=self.user, is_admin=True
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_data_handlowiec_is_valid(self):
        data = {k: v for k, v in self._valid_data().items() if k != "role"}
        form = UserUpdateForm(data=data, instance=self.user, is_admin=False)
        self.assertTrue(form.is_valid(), form.errors)

    def test_role_field_present_for_admin(self):
        form = UserUpdateForm(instance=self.user, is_admin=True)
        self.assertIn("role", form.fields)

    def test_role_field_absent_for_handlowiec(self):
        form = UserUpdateForm(instance=self.user, is_admin=False)
        self.assertNotIn("role", form.fields)

    def test_phone_optional(self):
        form = UserUpdateForm(
            data=self._valid_data(phone=""), instance=self.user, is_admin=True
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_role_choice(self):
        form = UserUpdateForm(
            data=self._valid_data(role="NIEZNANA"), instance=self.user, is_admin=True
        )
        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)

    def test_profile_phone_prefilled(self):
        self.user.profile.phone = "111222333"
        self.user.profile.save()
        form = UserUpdateForm(instance=self.user, is_admin=False)
        self.assertEqual(form.fields["phone"].initial, "111222333")
