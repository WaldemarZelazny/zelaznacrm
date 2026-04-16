"""Testy widokow aplikacji reports."""

from __future__ import annotations

import datetime
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage
from apps.reports.models import ActivityLog

# ---------------------------------------------------------------------------
# Pomocnicze funkcje
# ---------------------------------------------------------------------------


def _make_user(username: str, role: str = UserProfile.Role.HANDLOWIEC) -> User:
    user = User.objects.create_user(username=username, password="testpass")
    user.profile.role = role
    user.profile.save()
    return user


def _make_company(name: str, owner: User | None = None) -> Company:
    return Company.objects.create(name=name, owner=owner)


def _make_lead(
    title: str,
    company: Company,
    owner: User | None = None,
    status: str = Lead.Status.NOWY,
) -> Lead:
    stage, _ = WorkflowStage.objects.get_or_create(
        order=1, defaults={"name": "Nowy", "color": "#6c757d"}
    )
    return Lead.objects.create(
        title=title, company=company, owner=owner, stage=stage, status=status
    )


def _make_deal(
    title: str,
    company: Company,
    owner: User | None = None,
    value: str = "10000.00",
) -> Deal:
    return Deal.objects.create(
        title=title,
        company=company,
        owner=owner,
        value=value,
        close_date=datetime.date.today() + datetime.timedelta(days=30),
    )


def _make_log(
    user: User | None = None,
    action: str = ActivityLog.Action.UTWORZONO,
    model_name: str = "Lead",
) -> ActivityLog:
    return ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=1,
        object_repr="Lead #1",
    )


# ---------------------------------------------------------------------------
# Testy: przekierowanie niezalogowanych
# ---------------------------------------------------------------------------


class ReportsAuthRedirectTest(TestCase):
    """Niezalogowani musza byc przekierowani na login."""

    def _assert_redirect(self, url: str) -> None:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_dashboard_requires_login(self) -> None:
        self._assert_redirect(reverse("reports:dashboard"))

    def test_activity_requires_login(self) -> None:
        self._assert_redirect(reverse("reports:activity"))

    def test_sales_requires_login(self) -> None:
        self._assert_redirect(reverse("reports:sales"))


# ---------------------------------------------------------------------------
# Testy: blokada dla non-ADMIN
# ---------------------------------------------------------------------------


class ReportsAdminOnlyTest(TestCase):
    """Widoki reports dostepne tylko dla ADMIN — HANDLOWIEC dostaje 403."""

    def setUp(self) -> None:
        self.handlowiec = _make_user("non_admin")

    def test_dashboard_403_for_handlowiec(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_activity_403_for_handlowiec(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("reports:activity"))
        self.assertEqual(response.status_code, 403)

    def test_sales_403_for_handlowiec(self) -> None:
        self.client.force_login(self.handlowiec)
        response = self.client.get(reverse("reports:sales"))
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# Testy: ReportsDashboardView
# ---------------------------------------------------------------------------


class ReportsDashboardViewTest(TestCase):
    """Testy strony glownej raportow."""

    def setUp(self) -> None:
        self.admin = _make_user("dash_admin", role=UserProfile.Role.ADMIN)
        self.handlowiec = _make_user("dash_hw")
        self.company = _make_company("Dash Co", owner=self.handlowiec)
        _make_lead(
            "L1", self.company, owner=self.handlowiec, status=Lead.Status.WYGRANA
        )
        _make_lead("L2", self.company, owner=self.handlowiec, status=Lead.Status.NOWY)
        _make_deal("D1", self.company, owner=self.handlowiec, value="5000.00")

    def test_dashboard_returns_200_for_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_has_kpi_leads_total(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.context["kpi_leads_total"], 2)

    def test_dashboard_has_kpi_leads_won(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.context["kpi_leads_won"], 1)

    def test_dashboard_has_kpi_deals_total(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.context["kpi_deals_total"], 1)

    def test_dashboard_chart_lead_status_is_valid_json(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        data = json.loads(response.context["chart_lead_status"])
        self.assertIn("labels", data)
        self.assertIn("data", data)
        self.assertEqual(len(data["labels"]), len(data["data"]))

    def test_dashboard_chart_deal_status_is_valid_json(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        data = json.loads(response.context["chart_deal_status"])
        self.assertIn("labels", data)
        self.assertIn("data", data)

    def test_dashboard_chart_top_handlowcy_is_valid_json(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        data = json.loads(response.context["chart_top_handlowcy"])
        self.assertIn("labels", data)
        self.assertIn("data", data)

    def test_dashboard_chart_monthly_value_is_valid_json(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        data = json.loads(response.context["chart_monthly_value"])
        self.assertIn("labels", data)
        self.assertIn("data", data)

    def test_dashboard_context_has_is_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertTrue(response.context["is_admin"])


# ---------------------------------------------------------------------------
# Testy: ActivityLogListView
# ---------------------------------------------------------------------------


class ActivityLogListViewTest(TestCase):
    """Testy listy logow aktywnosci."""

    def setUp(self) -> None:
        self.admin = _make_user("log_admin", role=UserProfile.Role.ADMIN)
        self.user1 = _make_user("log_user1")
        self.user2 = _make_user("log_user2")
        self.log1 = _make_log(
            user=self.user1,
            action=ActivityLog.Action.UTWORZONO,
            model_name="Lead",
        )
        self.log2 = _make_log(
            user=self.user2,
            action=ActivityLog.Action.ZAKTUALIZOWANO,
            model_name="Company",
        )
        self.log3 = _make_log(
            user=self.user1,
            action=ActivityLog.Action.USUNIETO,
            model_name="Deal",
        )

    def test_activity_returns_200(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:activity"))
        self.assertEqual(response.status_code, 200)

    def test_activity_shows_all_logs(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:activity"))
        logs = list(response.context["logs"])
        self.assertIn(self.log1, logs)
        self.assertIn(self.log2, logs)
        self.assertIn(self.log3, logs)

    def test_filter_by_action(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("reports:activity"),
            {"action": ActivityLog.Action.UTWORZONO},
        )
        logs = list(response.context["logs"])
        self.assertIn(self.log1, logs)
        self.assertNotIn(self.log2, logs)
        self.assertNotIn(self.log3, logs)

    def test_filter_by_model_name(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:activity"), {"model_name": "Lead"})
        logs = list(response.context["logs"])
        self.assertIn(self.log1, logs)
        self.assertNotIn(self.log2, logs)

    def test_filter_by_username(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:activity"), {"user": "log_user2"})
        logs = list(response.context["logs"])
        self.assertIn(self.log2, logs)
        self.assertNotIn(self.log1, logs)
        self.assertNotIn(self.log3, logs)

    def test_context_has_action_choices(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:activity"))
        self.assertIn("action_choices", response.context)
        self.assertTrue(len(response.context["action_choices"]) > 0)

    def test_context_preserves_filter_values(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("reports:activity"),
            {"action": "UTWORZONO", "model_name": "Lead", "user": "log_user1"},
        )
        self.assertEqual(response.context["filter_action"], "UTWORZONO")
        self.assertEqual(response.context["filter_model"], "Lead")
        self.assertEqual(response.context["filter_user"], "log_user1")


# ---------------------------------------------------------------------------
# Testy: SalesReportView
# ---------------------------------------------------------------------------


class SalesReportViewTest(TestCase):
    """Testy raportu sprzedazowego."""

    def setUp(self) -> None:
        self.admin = _make_user("sales_admin", role=UserProfile.Role.ADMIN)
        self.hw1 = _make_user("sales_hw1")
        self.hw2 = _make_user("sales_hw2")
        self.company = _make_company("Sales Co", owner=self.hw1)
        _make_lead("L-won", self.company, owner=self.hw1, status=Lead.Status.WYGRANA)
        _make_lead("L-nowy", self.company, owner=self.hw1, status=Lead.Status.NOWY)
        _make_deal("D1", self.company, owner=self.hw1, value="20000.00")
        _make_deal("D2", self.company, owner=self.hw1, value="5000.00")

    def test_sales_returns_200(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        self.assertEqual(response.status_code, 200)

    def test_sales_context_has_rows(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        self.assertIn("rows", response.context)

    def test_sales_row_contains_hw1(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        users_in_rows = [row["user"] for row in response.context["rows"]]
        self.assertIn(self.hw1, users_in_rows)

    def test_sales_row_leads_count_correct(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        row = next(r for r in response.context["rows"] if r["user"] == self.hw1)
        self.assertEqual(row["leads_total"], 2)
        self.assertEqual(row["leads_won"], 1)

    def test_sales_row_deals_count_correct(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        row = next(r for r in response.context["rows"] if r["user"] == self.hw1)
        self.assertEqual(row["deals_total"], 2)

    def test_sales_row_deals_value_correct(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        row = next(r for r in response.context["rows"] if r["user"] == self.hw1)
        self.assertEqual(float(row["deals_value"]), 25000.0)

    def test_sales_row_conversion_correct(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        row = next(r for r in response.context["rows"] if r["user"] == self.hw1)
        # 1 won / 2 total = 50%
        self.assertEqual(row["conversion"], 50.0)

    def test_sales_hw_with_no_leads_has_zero_conversion(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        row = next(r for r in response.context["rows"] if r["user"] == self.hw2)
        self.assertEqual(row["conversion"], 0.0)

    def test_sales_sorted_by_value_desc(self) -> None:
        company2 = _make_company("Co2", owner=self.hw2)
        _make_deal("BigDeal", company2, owner=self.hw2, value="999999.00")
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        rows = response.context["rows"]
        values = [float(r["deals_value"]) for r in rows]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_sales_context_has_is_admin(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reports:sales"))
        self.assertTrue(response.context["is_admin"])
