"""URL routing dla aplikacji deals."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "deals"

urlpatterns = [
    path("", views.DealListView.as_view(), name="list"),
    path("add/", views.DealCreateView.as_view(), name="create"),
    path("<int:pk>/", views.DealDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.DealUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.DealDeleteView.as_view(), name="delete"),
    path("<int:pk>/complete/", views.DealCompleteView.as_view(), name="complete"),
    path("<int:pk>/cancel/", views.DealCancelView.as_view(), name="cancel"),
]
