"""Widoki aplikacji contacts – będą zaimplementowane w kolejnych krokach."""

from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ContactsListView(LoginRequiredMixin, TemplateView):
    """Stub widoku listy – placeholder przed pełną implementacją."""

    template_name = "placeholder.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["module_name"] = "contacts"
        return ctx
