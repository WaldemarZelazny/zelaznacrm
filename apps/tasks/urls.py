"""URL routing dla aplikacji tasks."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.TasksListView.as_view(), name="list"),
]
