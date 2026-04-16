"""Testy modelu ActivityLog aplikacji reports."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase

from apps.reports.models import ActivityLog

# ---------------------------------------------------------------------------
# Pomocnicza klasa-atrapa do testowania classmethod log()
# ---------------------------------------------------------------------------


class _FakeModel:
    """Prosta klasa imitujaca model Django na potrzeby testow."""

    def __init__(self, pk: int, repr_str: str) -> None:
        self.pk = pk
        self._repr = repr_str
        self.__class__.__name__ = "FakeModel"

    def __str__(self) -> str:
        return self._repr


# ---------------------------------------------------------------------------
# Testy __str__
# ---------------------------------------------------------------------------


class ActivityLogStrTest(TestCase):
    """Testy metody __str__ modelu ActivityLog."""

    def setUp(self) -> None:
        """Tworzy uzytkownika i podstawowy wpis logu."""
        self.user = User.objects.create_user(
            username="jan.kowalski",
            first_name="Jan",
            last_name="Kowalski",
        )

    def test_str_contains_action_model_and_user(self) -> None:
        """__str__ zawiera akcje, nazwe modelu i login uzytkownika."""
        log = ActivityLog.objects.create(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            model_name="Company",
            object_id=1,
            object_repr="Acme SA",
        )
        result = str(log)
        self.assertIn("UTWORZONO", result)
        self.assertIn("Company", result)
        self.assertIn("jan.kowalski", result)

    def test_str_uses_dash_when_no_user(self) -> None:
        """__str__ uzywa myslnika gdy brak uzytkownika."""
        log = ActivityLog.objects.create(
            user=None,
            action=ActivityLog.Action.USUNIETO,
            model_name="Lead",
            object_id=5,
            object_repr="Lead testowy",
        )
        self.assertIn("—", str(log))

    def test_str_contains_object_id(self) -> None:
        """__str__ zawiera ID obiektu."""
        log = ActivityLog.objects.create(
            action=ActivityLog.Action.WYSWIETLONO,
            model_name="Deal",
            object_id=42,
            object_repr="Umowa #42",
        )
        self.assertIn("#42", str(log))


# ---------------------------------------------------------------------------
# Testy classmethod log()
# ---------------------------------------------------------------------------


class ActivityLogLogMethodTest(TestCase):
    """Testy classmethod ActivityLog.log()."""

    def setUp(self) -> None:
        """Tworzy uzytkownika testowego."""
        self.user = User.objects.create_user(username="handlowiec")
        self.obj = _FakeModel(pk=7, repr_str="Firma Testowa Sp. z o.o.")

    def test_log_creates_entry_in_db(self) -> None:
        """log() zapisuje wpis do bazy danych."""
        ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.obj,
        )
        self.assertEqual(ActivityLog.objects.count(), 1)

    def test_log_fills_model_name_automatically(self) -> None:
        """log() wypelnia model_name na podstawie klasy obiektu."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.ZAKTUALIZOWANO,
            obj=self.obj,
        )
        self.assertEqual(entry.model_name, "FakeModel")

    def test_log_fills_object_repr_automatically(self) -> None:
        """log() wypelnia object_repr przez str(obj)."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.obj,
        )
        self.assertEqual(entry.object_repr, "Firma Testowa Sp. z o.o.")

    def test_log_stores_object_id(self) -> None:
        """log() poprawnie zapisuje object_id."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.obj,
        )
        self.assertEqual(entry.object_id, 7)

    def test_log_stores_user(self) -> None:
        """log() poprawnie przypisuje uzytkownika."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.WYSWIETLONO,
            obj=self.obj,
        )
        self.assertEqual(entry.user, self.user)

    def test_log_accepts_none_user(self) -> None:
        """log() przyjmuje None jako uzytkownika (akcja systemowa)."""
        entry = ActivityLog.log(
            user=None,
            action=ActivityLog.Action.USUNIETO,
            obj=self.obj,
        )
        self.assertIsNone(entry.user)

    def test_log_stores_description(self) -> None:
        """log() zapisuje opcjonalny opis zdarzenia."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.ZAKTUALIZOWANO,
            obj=self.obj,
            description="Zmieniono nazwe firmy.",
        )
        self.assertEqual(entry.description, "Zmieniono nazwe firmy.")

    def test_log_stores_ip_address(self) -> None:
        """log() zapisuje opcjonalny adres IP."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.WYSWIETLONO,
            obj=self.obj,
            ip="192.168.1.10",
        )
        self.assertEqual(entry.ip_address, "192.168.1.10")

    def test_log_default_description_is_empty(self) -> None:
        """log() domyslnie zapisuje pusty opis."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.obj,
        )
        self.assertEqual(entry.description, "")

    def test_log_truncates_long_repr(self) -> None:
        """log() obcina object_repr do 200 znakow."""
        long_obj = _FakeModel(pk=1, repr_str="X" * 300)
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=long_obj,
        )
        self.assertEqual(len(entry.object_repr), 200)

    def test_log_returns_activity_log_instance(self) -> None:
        """log() zwraca instancje ActivityLog."""
        entry = ActivityLog.log(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            obj=self.obj,
        )
        self.assertIsInstance(entry, ActivityLog)


# ---------------------------------------------------------------------------
# Testy wlasciwosci action_icon
# ---------------------------------------------------------------------------


class ActivityLogActionIconTest(TestCase):
    """Testy wlasciwosci action_icon."""

    def _make_log(self, action: str) -> ActivityLog:
        """Pomocnicza metoda tworzaca log z dana akcja."""
        return ActivityLog(
            action=action,
            model_name="Test",
            object_id=1,
            object_repr="Test",
        )

    def test_icon_for_utworzono(self) -> None:
        """action_icon zwraca checkmark dla UTWORZONO."""
        log = self._make_log(ActivityLog.Action.UTWORZONO)
        self.assertEqual(log.action_icon, "✅")

    def test_icon_for_zaktualizowano(self) -> None:
        """action_icon zwraca olowek dla ZAKTUALIZOWANO."""
        log = self._make_log(ActivityLog.Action.ZAKTUALIZOWANO)
        self.assertEqual(log.action_icon, "✏️")

    def test_icon_for_usunieto(self) -> None:
        """action_icon zwraca kosz dla USUNIETO."""
        log = self._make_log(ActivityLog.Action.USUNIETO)
        self.assertEqual(log.action_icon, "🗑️")

    def test_icon_for_wyswietlono(self) -> None:
        """action_icon zwraca oko dla WYSWIETLONO."""
        log = self._make_log(ActivityLog.Action.WYSWIETLONO)
        self.assertEqual(log.action_icon, "👁️")


# ---------------------------------------------------------------------------
# Testy pol i domyslnych wartosci
# ---------------------------------------------------------------------------


class ActivityLogFieldsTest(TestCase):
    """Testy pol modelu, wartosci domyslnych i zachowania przy usunieciu."""

    def setUp(self) -> None:
        """Tworzy uzytkownika testowego."""
        self.user = User.objects.create_user(username="test_user")

    def test_ip_address_optional(self) -> None:
        """Pole ip_address jest opcjonalne (null=True, blank=True)."""
        log = ActivityLog.objects.create(
            action=ActivityLog.Action.WYSWIETLONO,
            model_name="Task",
            object_id=10,
            object_repr="Zadanie #10",
        )
        self.assertIsNone(log.ip_address)

    def test_description_default_blank(self) -> None:
        """Pole description domyslnie puste."""
        log = ActivityLog.objects.create(
            action=ActivityLog.Action.UTWORZONO,
            model_name="Task",
            object_id=10,
            object_repr="Zadanie #10",
        )
        self.assertEqual(log.description, "")

    def test_set_null_on_user_delete(self) -> None:
        """Usuniecie uzytkownika ustawia user=NULL (SET_NULL)."""
        log = ActivityLog.objects.create(
            user=self.user,
            action=ActivityLog.Action.UTWORZONO,
            model_name="Note",
            object_id=3,
            object_repr="Notatka",
        )
        self.user.delete()
        log.refresh_from_db()
        self.assertIsNone(log.user)

    def test_created_at_auto_populated(self) -> None:
        """Pole created_at jest automatycznie ustawiane przy tworzeniu."""
        log = ActivityLog.objects.create(
            action=ActivityLog.Action.UTWORZONO,
            model_name="Company",
            object_id=1,
            object_repr="Firma",
        )
        self.assertIsNotNone(log.created_at)

    def test_ordering_newest_first(self) -> None:
        """Logi sortowane od najnowszego."""
        ActivityLog.objects.create(
            action=ActivityLog.Action.UTWORZONO,
            model_name="A",
            object_id=1,
            object_repr="Stary",
        )
        ActivityLog.objects.create(
            action=ActivityLog.Action.ZAKTUALIZOWANO,
            model_name="B",
            object_id=2,
            object_repr="Nowy",
        )
        self.assertEqual(ActivityLog.objects.first().object_repr, "Nowy")

    def test_action_choices_valid(self) -> None:
        """Wszystkie cztery wartosci Action.choices sa dostepne."""
        choices_values = [c[0] for c in ActivityLog.Action.choices]
        self.assertIn("UTWORZONO", choices_values)
        self.assertIn("ZAKTUALIZOWANO", choices_values)
        self.assertIn("USUNIETO", choices_values)
        self.assertIn("WYSWIETLONO", choices_values)
