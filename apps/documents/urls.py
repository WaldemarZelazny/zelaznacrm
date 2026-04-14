"""URL routing dla aplikacji documents."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentsListView.as_view(), name="list"),
]
