"""URL routing dla aplikacji leads."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path("", views.LeadListView.as_view(), name="list"),
    path("kanban/", views.LeadKanbanView.as_view(), name="kanban"),
    path("add/", views.LeadCreateView.as_view(), name="create"),
    path("<int:pk>/", views.LeadDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.LeadUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.LeadDeleteView.as_view(), name="delete"),
    path("<int:pk>/close/", views.LeadCloseView.as_view(), name="close"),
    path("export/xlsx/", views.LeadExportView.as_view(), name="export_xlsx"),
]
