"""Migracja danych – tworzy domyślne etapy lejka sprzedażowego.

6 etapów odpowiadających typowemu procesowi sprzedaży B2B:
Nowy → Kontakt → Oferta → Negocjacje → Wygrana / Przegrana.
"""

from __future__ import annotations

from django.db import migrations

DEFAULT_STAGES = [
    {"name": "Nowy", "order": 1, "color": "#6c757d"},  # szary
    {"name": "Kontakt", "order": 2, "color": "#0d6efd"},  # niebieski
    {"name": "Oferta", "order": 3, "color": "#fd7e14"},  # pomarańczowy
    {"name": "Negocjacje", "order": 4, "color": "#ffc107"},  # żółty
    {"name": "Wygrana", "order": 5, "color": "#198754"},  # zielony
    {"name": "Przegrana", "order": 6, "color": "#dc3545"},  # czerwony
]


def create_default_stages(apps, schema_editor):
    """Wstawia domyślne etapy lejka jeśli tabela jest pusta."""
    WorkflowStage = apps.get_model("leads", "WorkflowStage")
    if not WorkflowStage.objects.exists():
        WorkflowStage.objects.bulk_create(
            [WorkflowStage(**stage) for stage in DEFAULT_STAGES]
        )


def remove_default_stages(apps, schema_editor):
    """Usuwa domyślne etapy przy cofaniu migracji."""
    WorkflowStage = apps.get_model("leads", "WorkflowStage")
    names = [s["name"] for s in DEFAULT_STAGES]
    WorkflowStage.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):
    """Migracja danych: domyślne etapy WorkflowStage."""

    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_default_stages,
            reverse_code=remove_default_stages,
        ),
    ]
