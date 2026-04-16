"""URL routing dla aplikacji reports."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportsDashboardView.as_view(), name="dashboard"),
    path("activity/", views.ActivityLogListView.as_view(), name="activity"),
    path("sales/", views.SalesReportView.as_view(), name="sales"),
]
