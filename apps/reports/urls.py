"""URL routing dla aplikacji reports."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportsListView.as_view(), name="list"),
]
