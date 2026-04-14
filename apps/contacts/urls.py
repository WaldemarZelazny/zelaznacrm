"""URL routing dla aplikacji contacts."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    path("", views.ContactsListView.as_view(), name="list"),
]
