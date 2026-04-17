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
    # Profil zawsze istnieje (sygnał post_save), nie pokazujemy pustego formularza.
    extra = 0


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

    def save_formset(self, request, form, formset, change):
        # Sygnał post_save już utworzył UserProfile — używamy update_or_create
        # zamiast pozwolić inline zapisać nowy rekord (IntegrityError na UNIQUE).
        if formset.model is not UserProfile:
            super().save_formset(request, form, formset, change)
            return

        instances = formset.save(commit=False)
        for obj in instances:
            UserProfile.objects.update_or_create(
                user=obj.user,
                defaults={"role": obj.role, "phone": obj.phone, "avatar": obj.avatar},
            )
        formset.save_m2m()


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
