# Skill: PDF — Generowanie dokumentów PDF

## Cel
Generuj dokumenty PDF (oferty, umowy, protokoły) z szablonów HTML używając WeasyPrint.

## Stack
- **WeasyPrint** — konwersja HTML → PDF po stronie serwera
- **Django Template Language** — szablony dokumentów
- Model `Document` w `apps/documents/`

## Procedura implementacji

### 1. Szablon HTML dla PDF
Utwórz `templates/documents/pdf/<typ>_pdf.html`:
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    /* Style przeznaczone wyłącznie dla PDF — nie używaj Tablera */
    body { font-family: DejaVu Sans, sans-serif; font-size: 11pt; }
    .header { border-bottom: 2px solid #333; margin-bottom: 20px; }
  </style>
</head>
<body>
  <!-- treść dokumentu -->
</body>
</html>
```

### 2. Widok generujący PDF
```python
from django.http import HttpResponse
from weasyprint import HTML
from django.template.loader import render_to_string

def generate_pdf(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    html_string = render_to_string('documents/pdf/offer_pdf.html', {'doc': doc})
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dokument_{pk}.pdf"'
    return response
```

### 3. Czcionki dla polskich znaków
WeasyPrint wymaga DejaVu Sans lub innej czcionki z polskimi znakami.
Na Windows zainstaluj: `pip install weasyprint` (zawiera GTK z czcionkami).

## Uwagi
- Testuj PDF na danych z polskimi znakami (ą, ę, ś, ź, ż, ó, ć, ń, ł)
- Unikaj zewnętrznych zasobów CSS w szablonach PDF (brak internetu na produkcji)
- Używaj inline CSS lub `<style>` w szablonie
