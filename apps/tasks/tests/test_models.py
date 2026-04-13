"""Testy modelu Task aplikacji tasks."""

from __future__ import annotations

import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage
from apps.tasks.models import Task


def make_task(company, due_offset_hours: int = 24, **kwargs) -> Task:
    """Pomocnicza fabryka zadania testowego.

    Args:
        company: Firma powiazana z zadaniem.
        due_offset_hours: Przesuniecie terminu w godzinach od teraz
            (ujemne = przeszlosc).
        **kwargs: Dodatkowe pola nadpisujace wartosci domyslne.

    Returns:
        Zapisany obiekt Task.
    """
    defaults = {
        "title": "Zadanie testowe",
        "company": company,
        "due_date": timezone.now() + datetime.timedelta(hours=due_offset_hours),
    }
    defaults.update(kwargs)
    return Task.objects.create(**defaults)


class TaskStrTest(TestCase):
    """Testy metody __str__ modelu Task."""

    def setUp(self) -> None:
        """Tworzy podstawowe dane testowe."""
        self.company = Company.objects.create(name="Acme SA")

    def test_str_contains_type_title_and_due(self) -> None:
        """__str__ zawiera typ, tytul i termin zadania."""
        task = make_task(
            self.company,
            title="Zadzwon do klienta",
            task_type=Task.TaskType.TELEFON,
        )
        result = str(task)
        self.assertIn("Telefon", result)
        self.assertIn("Zadzwon do klienta", result)

    def test_str_default_type_is_zadanie(self) -> None:
        """Domyslny typ zadania to ZADANIE."""
        task = make_task(self.company)
        self.assertIn("Zadanie", str(task))


class TaskPropertiesTest(TestCase):
    """Testy wlasciwosci is_done i is_overdue."""

    def setUp(self) -> None:
        """Tworzy firme i zadania do testow."""
        self.company = Company.objects.create(name="Beta Corp")

    def test_is_done_false_for_new_task(self) -> None:
        """is_done == False dla nowego zadania."""
        task = make_task(self.company)
        self.assertFalse(task.is_done)

    def test_is_done_true_after_complete(self) -> None:
        """is_done == True po wykonaniu zadania."""
        task = make_task(self.company)
        task.complete()
        self.assertTrue(task.is_done)

    def test_is_overdue_false_for_future_due_date(self) -> None:
        """is_overdue == False gdy termin w przyszlosci."""
        task = make_task(self.company, due_offset_hours=24)
        self.assertFalse(task.is_overdue)

    def test_is_overdue_true_for_past_due_date(self) -> None:
        """is_overdue == True gdy termin minal i zadanie otwarte."""
        task = make_task(self.company, due_offset_hours=-1)
        self.assertTrue(task.is_overdue)

    def test_is_overdue_false_for_completed_task(self) -> None:
        """is_overdue == False dla wykonanego zadania, nawet po terminie."""
        task = make_task(self.company, due_offset_hours=-1)
        task.status = Task.Status.WYKONANE
        self.assertFalse(task.is_overdue)

    def test_is_overdue_false_for_cancelled_task(self) -> None:
        """is_overdue == False dla anulowanego zadania po terminie."""
        task = make_task(self.company, due_offset_hours=-1)
        task.status = Task.Status.ANULOWANE
        self.assertFalse(task.is_overdue)


class TaskCompleteMethodTest(TestCase):
    """Testy metody complete() modelu Task."""

    def setUp(self) -> None:
        """Tworzy otwarte zadanie do testow."""
        self.company = Company.objects.create(name="Gamma Inc")
        self.task = make_task(self.company, title="Do wykonania")

    def test_complete_sets_status_wykonane(self) -> None:
        """complete() ustawia status WYKONANE i zapisuje do bazy."""
        self.task.complete()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.WYKONANE)

    def test_complete_sets_completed_at(self) -> None:
        """complete() ustawia completed_at na biezacy czas."""
        before = timezone.now()
        self.task.complete()
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.completed_at)
        self.assertGreaterEqual(self.task.completed_at, before)

    def test_complete_preserves_existing_completed_at(self) -> None:
        """complete() nie nadpisuje completed_at gdy juz ustawione."""
        past = timezone.now() - datetime.timedelta(hours=5)
        self.task.completed_at = past
        self.task.save()
        self.task.complete()
        self.task.refresh_from_db()
        self.assertEqual(self.task.completed_at, past)

    def test_complete_raises_for_cancelled_task(self) -> None:
        """complete() rzuca ValueError dla anulowanego zadania."""
        self.task.status = Task.Status.ANULOWANE
        self.task.save()
        with self.assertRaises(ValueError):
            self.task.complete()


class TaskCancelMethodTest(TestCase):
    """Testy metody cancel() modelu Task."""

    def setUp(self) -> None:
        """Tworzy otwarte zadanie do testow."""
        self.company = Company.objects.create(name="Delta SA")
        self.task = make_task(self.company, title="Do anulowania")

    def test_cancel_sets_status_anulowane(self) -> None:
        """cancel() ustawia status ANULOWANE i zapisuje do bazy."""
        self.task.cancel()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.ANULOWANE)

    def test_cancel_idempotent(self) -> None:
        """cancel() na anulowanym zadaniu jest bezpieczne."""
        self.task.status = Task.Status.ANULOWANE
        self.task.save()
        self.task.cancel()
        self.assertEqual(self.task.status, Task.Status.ANULOWANE)

    def test_cancel_raises_for_completed_task(self) -> None:
        """cancel() rzuca ValueError dla wykonanego zadania."""
        self.task.status = Task.Status.WYKONANE
        self.task.save()
        with self.assertRaises(ValueError):
            self.task.cancel()


class TaskDefaultsAndRelationsTest(TestCase):
    """Testy wartosci domyslnych i relacji modelu Task."""

    def setUp(self) -> None:
        """Tworzy uzytkownikow i firme bazowa."""
        self.user = User.objects.create_user(username="handlowiec")
        self.company = Company.objects.create(name="Epsilon Corp")
        self.stage = WorkflowStage.objects.get(name="Nowy")

    def test_default_status_is_do_zrobienia(self) -> None:
        """Domyslny status to DO_ZROBIENIA."""
        task = make_task(self.company)
        self.assertEqual(task.status, Task.Status.DO_ZROBIENIA)

    def test_default_priority_is_sredni(self) -> None:
        """Domyslny priorytet to SREDNI."""
        task = make_task(self.company)
        self.assertEqual(task.priority, Task.Priority.SREDNI)

    def test_default_type_is_zadanie(self) -> None:
        """Domyslny typ to ZADANIE."""
        task = make_task(self.company)
        self.assertEqual(task.task_type, Task.TaskType.ZADANIE)

    def test_all_fk_optional(self) -> None:
        """Pola company, lead, deal, assigned_to, created_by sa opcjonalne."""
        task = Task.objects.create(
            title="Minimum",
            due_date=timezone.now() + datetime.timedelta(days=1),
        )
        self.assertIsNone(task.company)
        self.assertIsNone(task.lead)
        self.assertIsNone(task.deal)
        self.assertIsNone(task.assigned_to)
        self.assertIsNone(task.created_by)

    def test_set_null_on_company_delete(self) -> None:
        """Usuniecie firmy ustawia task.company=NULL (SET_NULL)."""
        task = make_task(self.company)
        self.company.delete()
        task.refresh_from_db()
        self.assertIsNone(task.company)

    def test_set_null_on_lead_delete(self) -> None:
        """Usuniecie leada ustawia task.lead=NULL (SET_NULL)."""
        lead = Lead.objects.create(
            title="Lead", company=Company.objects.create(name="X"), stage=self.stage
        )
        task = make_task(self.company, lead=lead)
        lead.delete()
        task.refresh_from_db()
        self.assertIsNone(task.lead)

    def test_set_null_on_deal_delete(self) -> None:
        """Usuniecie umowy ustawia task.deal=NULL (SET_NULL)."""
        import datetime as dt

        deal = Deal.objects.create(
            title="Deal",
            company=self.company,
            close_date=timezone.localdate() + dt.timedelta(days=7),
        )
        task = make_task(self.company, deal=deal)
        deal.delete()
        task.refresh_from_db()
        self.assertIsNone(task.deal)

    def test_ordering_by_due_date(self) -> None:
        """Zadania sortowane rosnaco po due_date."""
        make_task(self.company, title="Pozniejsze", due_offset_hours=48)
        make_task(self.company, title="Wczesniejsze", due_offset_hours=1)
        first = Task.objects.first()
        self.assertEqual(first.title, "Wczesniejsze")
