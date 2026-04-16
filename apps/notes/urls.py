"""URL routing dla aplikacji notes."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "notes"

urlpatterns = [
    path("", views.NoteListView.as_view(), name="list"),
    path("add/", views.NoteCreateView.as_view(), name="create"),
    path("<int:pk>/", views.NoteDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.NoteUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.NoteDeleteView.as_view(), name="delete"),
]
