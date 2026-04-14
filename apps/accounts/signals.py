"""Sygnały aplikacji accounts – automatyczne tworzenie UserProfile."""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(
    sender: type[User],
    instance: User,
    created: bool,
    **kwargs,
) -> None:
    """Tworzy UserProfile automatycznie po utworzeniu nowego User.

    Sygnał post_save nasłuchuje tylko dla nowo zapisanych obiektów
    (created=True). Aktualizacje istniejących userów są ignorowane,
    aby nie nadpisywać danych profilu.

    Args:
        sender: Klasa modelu wysyłającego sygnał (User).
        instance: Nowo utworzony obiekt User.
        created: True gdy obiekt został właśnie utworzony (nie edytowany).
        **kwargs: Dodatkowe argumenty przekazywane przez Django.
    """
    if created:
        UserProfile.objects.create(user=instance)
        logger.info(
            "Automatycznie utworzono UserProfile dla użytkownika: %s",
            instance.username,
        )
