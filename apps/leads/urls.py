"""URL routing dla aplikacji leads."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.LeadsListView.as_view(), name="list"),
]
