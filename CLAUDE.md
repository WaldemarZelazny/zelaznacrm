# Instrukcje dla Projektu Dyplomowego (Django CRM)

Jesteś asystentem programowania wspomagającym tworzenie aplikacji webowej CRM w ramach pracy dyplomowej.
Preferuj narzędzia, metodologię i standardy opisane poniżej. Jeśli jednak w konkretnej sytuacji
istnieje bardziej optymalne rozwiązanie spoza tych wytycznych, możesz z niego skorzystać —
z krótkim uzasadnieniem dlaczego jest lepszym wyborem.

---

## 1. Stack Technologiczny

- **Framework:** Django 5.x (wzorzec architektoniczny MVT: Model-View-Template)
- **Język:** Python 3.12+
- **Baza danych:** PostgreSQL (produkcja), SQLite (lokalne testy)
- **ORM:** Django ORM (menedżer `objects`, nigdy surowy SQL bez powodu)
- **Migracje:** wbudowany system Django (`makemigrations`, `migrate`)
- **Frontend:** Bootstrap 5 via **Tabler** (https://github.com/tabler/tabler)
- **Szablony:** Django Template Language (DTL), dziedziczenie (`{% extends %}`, `{% block %}`)
- **Formularze:** Django Forms + `django-crispy-forms` z layoutem Tabler/Bootstrap 5
- **PDF:** `weasyprint` — generowanie ofert i umów z szablonów HTML
- **Scraping:** Playwright + beautifulsoup4 (analiza systemu RRUP)

---

## 2. Standardy Kodowania i Jakość

### Styl kodu (PEP 8)
- Klasy: `PascalCase` | Funkcje i zmienne: `snake_case` | Stałe: `UPPER_SNAKE_CASE`
- Maksymalna długość linii: **88 znaków** (Black formatter)
- Dwa puste wiersze między klasami/funkcjami najwyższego poziomu
- Jeden pusty wiersz między metodami klasy

### Typowanie (Type Hints)
```python
from typing import Optional

def get_user(user_id: int) -> Optional[User]:
    ...
```
- Używaj `from __future__ import annotations` dla opóźnionej ewaluacji

### Dokumentacja (Docstrings — Google Style)
```python
def create_lead(title: str, owner: User) -> Lead:
    """Tworzy nowy lead sprzedażowy.

    Args:
        title: Tytuł leada (maks. 200 znaków).
        owner: Użytkownik będący właścicielem leada.

    Returns:
        Nowo utworzony obiekt Lead.

    Raises:
        ValueError: Jeśli tytuł jest pusty.
    """
```

### Obsługa błędów
- Łap **konkretne** wyjątki — nigdy gołe `except:` ani `except Exception:` bez logowania
- Używaj wyjątków Django: `Http404`, `PermissionDenied`, `ObjectDoesNotExist`
```python
try:
    lead = Lead.objects.get(pk=lead_id)
except Lead.DoesNotExist:
    raise Http404("Lead nie istnieje.")
```

### Logowanie
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Użytkownik %s utworzył lead: %s", user.username, lead.title)
logger.error("Błąd zapisu leada: %s", exc, exc_info=True)
```
- **Nigdy** nie używaj `print()` w kodzie produkcyjnym

### Inne zasady
- f-stringi zamiast `.format()` lub `%`
- `pathlib.Path` zamiast `os.path`
- Unikaj "magicznych liczb" — używaj `IntegerChoices` lub stałych

---

## 3. Workflow i Kontrola Wersji (Git)

### Conventional Commits
Format: `<type>(<scope>): <description>`

| Typ | Znaczenie |
|-----|-----------|
| `feat` | Nowa funkcjonalność |
| `fix` | Poprawka błędu |
| `docs` | Zmiany w dokumentacji |
| `style` | Formatowanie, bez zmian logiki |
| `refactor` | Refaktoryzacja |
| `test` | Testy |
| `chore` | Konfiguracja, zależności |

Przykłady: `feat(leads): add kanban board view`, `fix(auth): correct login redirect`

### Git Flow
- `main` — kod produkcyjny
- `develop` — integracja funkcji
- `feature/nazwa` — nowe funkcjonalności
- `hotfix/nazwa` — krytyczne poprawki

### Atomowość
Jeden commit = jedna logiczna zmiana. Commituj po każdym ukończonym module.

---

## 4. Architektura Django (MVT)

### Separacja warstw
- `models.py` — definicje danych i logika domenowa
- `views.py` — obsługa żądań HTTP (bez logiki biznesowej)
- `services.py` — warstwa serwisowa dla złożonej logiki biznesowej
- `forms.py` — walidacja i przetwarzanie danych wejściowych
- `urls.py` — routing URL per aplikacja
- `admin.py` — konfiguracja panelu administracyjnego
- `tests/` — katalog z testami (test_models.py, test_views.py, test_forms.py)

### Class-Based Views (CBV) — preferowane
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "leads/lead_list.html"
    context_object_name = "leads"
    paginate_by = 20

    def get_queryset(self):
        return Lead.objects.select_related("owner", "company").filter(
            owner=self.request.user
        )
```
- FBV tylko dla złożonej, niestandardowej logiki

### Django Admin
```python
@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "status", "created_at")
    list_filter = ("status", "source")
    search_fields = ("title", "owner__username")
```

### Optymalizacja zapytań (N+1)
```python
# ZAWSZE używaj select_related / prefetch_related w widokach list
Lead.objects.select_related("owner", "company").prefetch_related("tasks")
```
Sprawdzaj liczbę zapytań w django-debug-toolbar po każdym widoku listy.

---

## 5. Bezpieczeństwo i Konfiguracja

### Zmienne środowiskowe
- `SECRET_KEY`, hasła DB, klucze API — WYŁĄCZNIE w pliku `.env`
- Wczytuj przez `django-environ`
- Plik `.env` MUSI być w `.gitignore`
- Dołącz `.env.example` z przykładowymi kluczami (bez wartości)

### Zabezpieczenia formularzy
- Zawsze `{% csrf_token %}` w formularzach POST
- Waliduj WSZYSTKIE dane od użytkownika przez Django Forms

### Ustawienia produkcyjne
```python
DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
```

---

## 6. Testowanie

- Framework: `pytest-django` + `factory-boy` + `Faker` (locale `pl_PL`)
- Cel: minimum **70% pokrycia kodu** (`pytest --cov=apps --cov-report=html`)
- Organizacja: katalog `tests/` z podziałem na `test_models.py`, `test_views.py`, `test_forms.py`

```python
from django.test import TestCase
from django.urls import reverse

class LeadListViewTest(TestCase):
    def test_login_required(self) -> None:
        response = self.client.get(reverse("leads:list"))
        self.assertEqual(response.status_code, 302)

    def test_returns_200_for_logged_user(self) -> None:
        self.client.force_login(UserFactory())
        response = self.client.get(reverse("leads:list"))
        self.assertEqual(response.status_code, 200)
```

---

## 7. Struktura Projektu

```
ZelaznaCRM/
├── manage.py
├── .env                        # NIE w repozytorium
├── .env.example
├── .gitignore
├── CLAUDE.md                   # Ten plik
├── CONTEXT.md                  # Kontekst projektu
├── README.md
├── CHANGELOG.md
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/               # Użytkownicy i role
│   ├── companies/              # Firmy
│   ├── contacts/               # Kontakty
│   ├── leads/                  # Leady i lejek sprzedażowy
│   ├── deals/                  # Umowy i transakcje
│   ├── tasks/                  # Zadania i aktywności
│   ├── documents/              # Dokumenty i PDF
│   ├── notes/                  # Notatki
│   └── reports/                # Raporty i logi
├── templates/
│   ├── base.html               # Strona startowa (landing page)
│   ├── base_dashboard.html     # Baza dla panelu po zalogowaniu
│   ├── components/             # Reużywalne fragmenty UI
│   └── [app_name]/
├── static/
│   ├── tabler/                 # Pliki Tabler CSS/JS
│   ├── css/
│   ├── js/
│   └── img/
└── .claude/
    └── skills/                 # Agent skills dla Claude Code
```

---

## 8. Narzędzia Deweloperskie

| Narzędzie | Cel |
|-----------|-----|
| `black` | Automatyczne formatowanie kodu |
| `flake8` | Linter PEP 8 |
| `isort` | Sortowanie importów |
| `mypy` + `django-stubs` | Statyczna analiza typów |
| `pre-commit` | Automatyczne sprawdzenia przed commitem |
| `django-debug-toolbar` | Debugowanie zapytań SQL |
| `django-extensions` | Dodatkowe komendy manage.py (`shell_plus`) |

### Konfiguracja pre-commit (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

---

## 9. Agent Skills (Claude Code)

Repozytorium: https://github.com/VoltAgent/awesome-agent-skills
Folder lokalny: `.claude/skills/`

| Skill | Kiedy używać |
|-------|-------------|
| `openai/playwright-interactive` | Faza 1 – scraping RRUP |
| `openai/frontend-skill` | Faza 5 – landing page i szablony |
| `garrytan/qa` | Faza 6 – testowanie |
| `garrytan/ship` | Po każdym module – commit i push |
| `garrytan/document-release` | Po każdej fazie – aktualizacja docs |

---

## 10. Zasady Ogólne

- **DRY** — nie powtarzaj kodu
- **KISS** — prostota przed elegancją
- **YAGNI** — nie implementuj "na zapas"
- **Single Responsibility** — każda klasa/funkcja ma jeden cel
- Używaj `IntegerChoices` dla pól wyboru w modelach
- Przy każdym większym bloku kodu dodaj komentarz wyjaśniający **dlaczego**
- Używaj polskich `verbose_name` w modelach i interfejsie użytkownika
- Projekt jest **inspirowany** RRUP — odwzorowujemy funkcjonalność, nie kopiujemy kodu
- Jeśli napotkasz coś czego nie ma w planie — zapytaj użytkownika przed implementacją
