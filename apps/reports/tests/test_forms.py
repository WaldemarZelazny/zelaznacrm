"""Testy formularzy aplikacji reports."""

from __future__ import annotations

from django.test import TestCase

from apps.reports.forms import ActivityLogFilterForm
from apps.reports.models import ActivityLog


class ActivityLogFilterFormTest(TestCase):
    # --- Poprawne dane ---

    def test_empty_form_is_valid(self):
        form = ActivityLogFilterForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_action_is_valid(self):
        form = ActivityLogFilterForm(data={"action": ActivityLog.Action.UTWORZONO})
        self.assertTrue(form.is_valid(), form.errors)

    def test_all_fields_filled_is_valid(self):
        form = ActivityLogFilterForm(
            data={
                "action": ActivityLog.Action.ZAKTUALIZOWANO,
                "model_name": "Lead",
                "user": "handlowiec",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Poszczegolne pola opcjonalne ---

    def test_action_empty_is_valid(self):
        form = ActivityLogFilterForm(data={"action": "", "model_name": "", "user": ""})
        self.assertTrue(form.is_valid(), form.errors)

    def test_model_name_only_is_valid(self):
        form = ActivityLogFilterForm(
            data={"action": "", "model_name": "Company", "user": ""}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_user_only_is_valid(self):
        form = ActivityLogFilterForm(
            data={"action": "", "model_name": "", "user": "jan"}
        )
        self.assertTrue(form.is_valid(), form.errors)

    # --- Niepoprawne wartosci ---

    def test_invalid_action_choice_invalid(self):
        form = ActivityLogFilterForm(data={"action": "NIEZNANA_AKCJA"})
        self.assertFalse(form.is_valid())
        self.assertIn("action", form.errors)

    # --- Wszystkie wartosci Action sa akceptowane ---

    def test_all_action_choices_valid(self):
        for value, _ in ActivityLog.Action.choices:
            form = ActivityLogFilterForm(data={"action": value})
            self.assertTrue(
                form.is_valid(), f"Akcja {value} powinna byc poprawna: {form.errors}"
            )

    # --- cleaned_data ---

    def test_cleaned_data_action(self):
        form = ActivityLogFilterForm(data={"action": ActivityLog.Action.USUNIETO})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["action"], ActivityLog.Action.USUNIETO)

    def test_cleaned_data_model_name(self):
        form = ActivityLogFilterForm(
            data={"action": "", "model_name": "Deal", "user": ""}
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["model_name"], "Deal")
