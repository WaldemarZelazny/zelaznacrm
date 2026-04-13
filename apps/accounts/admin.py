"""Konfiguracja panelu administracyjnego dla aplikacji accounts."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline profilu w panelu edycji użytkownika."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = _("profil")
    fields = ("role", "phone", "avatar")


class UserAdmin(BaseUserAdmin):
    """Rozszerzony panel użytkownika – wbudowany profil CRM."""

    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_role",
        "is_active",
    )
    list_filter = ("is_active", "is_staff", "profile__role")

    @admin.display(description=_("Rola CRM"), ordering="profile__role")
    def get_role(self, obj: User) -> str:
        """Zwraca rolę CRM przypisaną do użytkownika."""
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return "—"


# Zastępujemy domyślny UserAdmin rozszerzonym
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Panel administracyjny profili użytkowników."""

    list_display = ("user", "role", "phone", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")
    readonly_fields = ("created_at",)
    ordering = ("user__last_name", "user__first_name")
