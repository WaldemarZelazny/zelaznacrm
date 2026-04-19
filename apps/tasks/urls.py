"""URL routing dla aplikacji tasks."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.TaskListView.as_view(), name="list"),
    path("calendar/", views.TaskCalendarView.as_view(), name="calendar"),
    path("add/", views.TaskCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TaskDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.TaskUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.TaskDeleteView.as_view(), name="delete"),
    path("<int:pk>/complete/", views.TaskCompleteView.as_view(), name="complete"),
    path("<int:pk>/cancel/", views.TaskCancelView.as_view(), name="cancel"),
    path("export/xlsx/", views.TaskExportView.as_view(), name="export_xlsx"),
]
