"""URL routing dla aplikacji deals."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "deals"

urlpatterns = [
    path("", views.DealsListView.as_view(), name="list"),
]
