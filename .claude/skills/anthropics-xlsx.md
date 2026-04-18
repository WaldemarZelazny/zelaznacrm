# Skill: XLSX — Eksport danych do Excela

## Cel
Eksportuj dane (raporty, listy leadów, firmy) do pliku Excel (.xlsx) używając openpyxl.

## Stack
- **openpyxl** — generowanie plików .xlsx
- Dodaj do `requirements/base.txt`: `openpyxl>=3.1.0`

## Procedura implementacji

### 1. Instalacja
```bash
pip install openpyxl
echo "openpyxl>=3.1.0" >> requirements/base.txt
```

### 2. Widok eksportu
```python
import openpyxl
from django.http import HttpResponse

def export_leads_xlsx(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Leady"

    # Nagłówki
    headers = ["Tytuł", "Firma", "Status", "Wartość", "Data utworzenia"]
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)

    # Dane
    leads = Lead.objects.select_related("company").filter(owner=request.user)
    for row, lead in enumerate(leads, 2):
        ws.cell(row=row, column=1, value=lead.title)
        ws.cell(row=row, column=2, value=lead.company.name if lead.company else "")
        ws.cell(row=row, column=3, value=lead.get_status_display())
        ws.cell(row=row, column=4, value=float(lead.value) if lead.value else 0)
        ws.cell(row=row, column=5, value=lead.created_at.strftime("%Y-%m-%d"))

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="leady.xlsx"'
    wb.save(response)
    return response
```

### 3. URL
```python
path("export/xlsx/", views.export_leads_xlsx, name="export_xlsx"),
```

## Uwagi
- Używaj `select_related` / `prefetch_related` — eksport może dotyczyć tysięcy rekordów
- Ogranicz eksport do danych bieżącego użytkownika (HANDLOWIEC) lub wszystkich (ADMIN)
- Dodaj link eksportu w widoku listy: `<a href="{% url 'leads:export_xlsx' %}">Eksportuj XLSX</a>`
