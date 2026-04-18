# Skill: QA — Testowanie i zapewnienie jakości

## Cel
Przeprowadź kompleksowe testy zaimplementowanej funkcjonalności przed commitem.

## Procedura

### 1. Testy automatyczne
```bash
pytest --tb=short -q
pytest --cov=apps --cov-report=term-missing --cov-fail-under=70
```

### 2. Weryfikacja statyczna
```bash
black --check .
flake8 apps/
```

### 3. Testy manualne (serwer)
- Uruchom `python manage.py runserver`
- Przetestuj golden path (szczęśliwa ścieżka)
- Przetestuj edge cases (puste formularze, brak uprawnień, 404)
- Sprawdź widok dla roli ADMIN i HANDLOWIEC
- Sprawdź responsywność (mobile viewport)

### 4. Weryfikacja bezpieczeństwa
- Czy każdy widok ma `LoginRequiredMixin`?
- Czy formularze POST mają `{% csrf_token %}`?
- Czy HANDLOWIEC nie może zobaczyć danych innych handlowców?

### 5. Raport
Podsumuj: ile testów przeszło, jakie edge cases pokryto, czy są znane ograniczenia.
