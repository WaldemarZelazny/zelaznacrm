"""URL routing dla aplikacji companies."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "companies"

urlpatterns = [
    path("", views.CompaniesListView.as_view(), name="list"),
]
