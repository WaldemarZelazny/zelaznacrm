# ZelaznaCRM — Podsumowanie projektu

> Dokument do wykorzystania jako baza przy kolejnych projektach Django.
> Zawiera wnioski, sprawdzone wzorce i gotowe szablony startowe.

---

## 1. Dane projektu

| Pole | Wartość |
|------|---------|
| **Nazwa** | ZelaznaCRM |
| **Typ** | Aplikacja webowa CRM (Customer Relationship Management) |
| **Cel** | Projekt dyplomowy — system CRM dla małych zespołów sprzedażowych |
| **Autor** | Waldemar Żelazny |
| **Data realizacji** | 13–23 kwietnia 2026 (10 dni roboczych) |
| **Repozytorium** | https://github.com/WaldemarZelazny/zelaznacrm |
| **Ostatni commit** | `32a7176` (2026-04-23) |

### Stack technologiczny

| Warstwa | Technologia | Wersja |
|---------|-------------|--------|
| Framework | Django | 6.0.2 |
| Język | Python | 3.14 |
| Baza danych (dev) | SQLite | wbudowana |
| Baza danych (prod) | PostgreSQL | 14+ |
| Frontend | Tabler + Bootstrap 5 | Tabler 1.x |
| Formularze | django-crispy-forms + crispy-bootstrap5 | 2.1 / 2024.2 |
| PDF | WeasyPrint | 62.3 |
| Excel | openpyxl | 3.1.2 |
| HTTP klient | requests | 2.31+ |
| Obrazy | Pillow | 10.3+ |
| Env vars | django-environ | 0.11+ |
| Debug | django-debug-toolbar | 4.3+ |
| Testy | pytest-django | 4.8+ |
| Linter | flake8 + black + isort | 7.0 / 24.3 / 5.13 |
| Dokumentacja | Sphinx + sphinx-rtd-theme | 9.0+ |

---

## 2. Statystyki projektu

| Kategoria | Pliki | Linie kodu |
|-----------|------:|----------:|
| Python — kod aplikacji | 93 | ~8 500 |
| Python — testy | 36 | ~7 579 |
| HTML szablony | 44 | ~5 636 |
| Dokumentacja (MD/RST) | 140+ | ~3 634 |
| **Kod własny łącznie** | **313+** | **~25 349** |
| CSS/JS vendor (Tabler) | ~60 | ~64 000 |

### Testy

| Metryka | Wartość |
|---------|---------|
| Łączna liczba testów | **664** |
| Wynik | 664 passed, 0 failed |
| Pokrycie aplikacji | 9 / 9 (100%) |
| Udział testów w kodzie | **46%** |
| Pliki testowe | 27 (3 per aplikacja) |

### Git

| Metryka | Wartość |
|---------|---------|
| Łączna liczba commitów | 73 |
| Czas realizacji | 10 dni (13–23 IV 2026) |
| Gałęzie | main, develop, feature/* |
| Standard commitów | Conventional Commits |

### Fazy projektu

| Faza | Zakres | Czas |
|------|--------|------|
| Faza 1 | Analiza RRUP (Playwright scraping) | Przed projektem |
| Faza 2 | Inicjalizacja, konfiguracja | 13–14 IV |
| Faza 3 | Modele (9 aplikacji, 11 modeli) | 14 IV |
| Faza 4 | Widoki CBV + formularze + szablony | 14–16 IV |
| Faza 5 | Seed data, NIP lookup, raporty XLSX/PDF | 16–17 IV |
| Faza 6 | Testy (664 testów) | 19 IV |
| Faza 7 | Poprawki, dokumentacja, ERD, instrukcje | 20–23 IV |

---

## 3. Architektura

### Struktura katalogów

```
ZelaznaCRM/
├── manage.py
├── .env / .env.example
├── requirements/
│   ├── base.txt          # produkcja
│   ├── development.txt   # dev + testy + linting + docs
│   └── production.txt    # + gunicorn + whitenoise
├── config/
│   ├── settings/
│   │   ├── base.py       # wspólne ustawienia
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/         # User + UserProfile, logowanie, role
│   ├── companies/        # Firmy + NIP lookup
│   ├── contacts/         # Osoby kontaktowe
│   ├── leads/            # Lejek + WorkflowStage + Kanban
│   ├── deals/            # Umowy handlowe
│   ├── tasks/            # Zadania + kalendarz FullCalendar
│   ├── documents/        # Pliki + generowanie PDF
│   ├── notes/            # Notatki wielopowiązaniowe
│   └── reports/          # ActivityLog + raport XLSX
├── templates/
│   ├── base.html         # landing page
│   ├── base_dashboard.html  # baza panelu (sidebar, topbar, messages)
│   └── [app_name]/
├── static/
│   ├── css/custom.css
│   ├── img/zelaznaCRM.ico
│   └── tabler/           # vendor CSS/JS
└── docs/                 # Sphinx autodoc (131 plików RST)
```

### Modele i relacje

| Model | Aplikacja | Kluczowe FK |
|-------|-----------|-------------|
| User | django.auth | — |
| UserProfile | accounts | User (1:1) |
| Company | companies | User (owner) |
| Contact | contacts | Company, User |
| WorkflowStage | leads | — |
| Lead | leads | Company, Contact, User, WorkflowStage |
| Deal | deals | Company, Lead, User |
| Task | tasks | Company, Lead, Deal, User×2 |
| Document | documents | Company, Lead, Deal, User |
| Note | notes | User, Company, Lead, Deal, Contact |
| ActivityLog | reports | User |

Diagram ERD: [ERD.md](ERD.md) | [ERD.png](ERD.png)

### Wzorce użyte w projekcie

| Wzorzec | Gdzie | Opis |
|---------|-------|------|
| **CBV** | Wszystkie 54 widoki | ListView, DetailView, CreateView, UpdateView, DeleteView |
| **LoginRequiredMixin** | Wszystkie widoki | Ochrona przed dostępem anonimowym |
| **post_save signal** | accounts/signals.py | Auto-tworzenie UserProfile po rejestracji User |
| **TextChoices** | Wszystkie modele z polami wyboru | Role, statusy, typy — enum w modelu |
| **select_related** | Widoki listowe | Eliminacja zapytań N+1 |
| **get_queryset override** | Widoki listowe | Filtrowanie per rola (ADMIN widzi wszystko, HANDLOWIEC tylko swoje) |
| **form_valid override** | CreateView | Auto-ustawianie owner=request.user |
| **SimpleListFilter** | admin tasks/notes | Własne filtry: OverdueFilter, RelationFilter |
| **update_or_create** | admin accounts | Bezpieczny zapis inline UserProfile |
| **messages framework** | Każda akcja CRUD | Powiadomienia success/error w UI |

---

## 4. Narzędzia i biblioteki

### Co się sprawdziło ✅

| Narzędzie | Ocena | Uwaga |
|-----------|-------|-------|
| **Django 6.x** | ★★★★★ | Stabilny, szybki development. Uwaga: zmiany vs 5.x (patrz sekcja 6) |
| **Tabler UI** | ★★★★★ | Gotowe komponenty: sidebar, kanban, kalendarze, tabele, formularze |
| **pytest-django** | ★★★★★ | Szybsze niż TestCase, fixtures przez fabryki |
| **pre-commit** | ★★★★☆ | Automatyczne formatowanie przed commitem — nieocenione |
| **django-crispy-forms** | ★★★★☆ | Bootstrap 5 formularze bez pisania HTML |
| **WeasyPrint** | ★★★★☆ | Generowanie PDF z HTML/CSS — prosty setup |
| **openpyxl** | ★★★★★ | Eksport XLSX z nagłówkami, formatowaniem — niezawodny |
| **django-environ** | ★★★★★ | Wczytywanie .env, type-safe |
| **Sphinx + RTD** | ★★★☆☆ | Dobre do autodoc, ale wymaga poprawnej konfiguracji mock imports |
| **black** | ★★★★★ | Zero konfiguracji, determinizm formatowania |

### Co było problematyczne ⚠️

| Narzędzie | Problem | Rozwiązanie |
|-----------|---------|-------------|
| **CEIDG API** | v2 wyłączone 1.10.2025 | Zmiana URL na v3, fallback na Białą Listę MF dla spółek |
| **sphinxcontrib-django** | Instaluje się jako `sphinxcontrib_django` (podkreślnik) | Użyć `sphinxcontrib_django` w conf.py, nie `sphinxcontrib.django` |
| **Sphinx + Django apps** | `RuntimeError: Model doesn't declare app_label` | `autodoc_mock_imports` dla wszystkich zależności Django |
| **matplotlib ICO** | `frames[0].save(..., append_images=...)` zapisywał tylko 1 frame | Budowanie ICO binarnie przez `struct` + PNG w buforach |
| **flake8 E402** | Stała przed importami (`_XLSX_CONTENT_TYPE`) | Przenieść stałą za ostatni import |
| **Django Admin + signal** | `IntegrityError` — sygnał i inline tworzyły profil 2x | `extra=0` + `update_or_create` w `save_formset` |

---

## 5. Kluczowe rozwiązania techniczne

### 5.1 Autouzupełnianie NIP

Podejście server-side (GET/POST na `/companies/nip-search/`) zamiast AJAX — niezawodne, bez konfliktów z Tablerem.

```python
# apps/companies/views.py — NipSearchView
def get(self, request):
    nip = request.GET.get("nip", "").strip()
    if nip:
        data = fetch_nip_data(nip)  # próbuje CEIDG v3, fallback MF
        return render(request, "companies/nip_search.html", {"data": data, "nip": nip})

# Kolejność źródeł:
# 1. CEIDG v3: https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nip={nip}  (JDG)
# 2. Biała Lista MF: https://wl-api.mf.gov.pl/?nip={nip}  (spółki, bez tokenu)
```

### 5.2 ActivityLog — niemutowalny dziennik zdarzeń

```python
# apps/reports/models.py
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20)   # CREATE/UPDATE/DELETE/VIEW
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    ip_address = models.GenericIPAddressField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

# Użycie w widoku (mixin):
ActivityLog.objects.create(
    user=request.user,
    action="CREATE",
    model_name=self.model.__name__,
    object_id=obj.pk,
    object_repr=str(obj),
    ip_address=request.META.get("REMOTE_ADDR"),
)
```

### 5.3 Eksport XLSX

```python
# apps/reports/views.py — wzorzec eksportu
def export_xlsx(queryset, filename, headers, row_getter):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for obj in queryset:
        ws.append(row_getter(obj))
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
```

### 5.4 Generowanie PDF (WeasyPrint)

```python
# apps/documents/views.py
from weasyprint import HTML

def generate_pdf(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    html_string = render_to_string("documents/pdf_template.html", {"doc": doc})
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{doc.title}.pdf"'
    return response
```

### 5.5 Kanban (WorkflowStage)

```python
# apps/leads/views.py — KanbanView
class KanbanView(LoginRequiredMixin, TemplateView):
    template_name = "leads/kanban.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        stages = WorkflowStage.objects.filter(is_active=True).order_by("order")
        qs = Lead.objects.select_related("company", "owner", "stage")
        if not self.request.user.profile.role == "ADMIN":
            qs = qs.filter(owner=self.request.user)
        ctx["columns"] = [
            {"stage": s, "leads": qs.filter(stage=s)} for s in stages
        ]
        return ctx
```

### 5.6 Sygnał post_save dla UserProfile

```python
# apps/accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

# apps/accounts/apps.py — rejestracja sygnału
class AccountsConfig(AppConfig):
    def ready(self):
        import apps.accounts.signals  # noqa: F401
```

### 5.7 Filtrowanie per rola użytkownika

```python
# Wzorzec stosowany w każdym get_queryset()
def get_queryset(self):
    qs = super().get_queryset().select_related("owner", "company")
    if self.request.user.profile.role != UserProfile.Role.ADMIN:
        qs = qs.filter(owner=self.request.user)
    return qs
```

---

## 6. Lekcje z projektu (Top 5)

### L1. Stary proces Django serwuje stary kod
**Problem:** Zmiany w kodzie nie są widoczne w przeglądarce.
**Przyczyna:** Wiele starych procesów python.exe na porcie 8000.
**Rozwiązanie:** `taskkill /F /IM python.exe` (Windows) przed każdym restartem.

### L2. CEIDG API v2 wyłączone — zawsze weryfikuj URL zewnętrznych API
**Problem:** API zwracało 404 dla każdego NIP po 1.10.2025.
**Rozwiązanie:** Zmień URL na v3. Dodaj fallback na inne źródło (Biała Lista MF).
**Wniosek ogólny:** Zewnętrzne API mogą zmienić wersję bez ostrzeżenia — zawsze miej fallback.

### L3. Django 6.0 — dostęp do atrybutu None w szablonach rzuca wyjątek
**Problem:** `{{ obj.attr|default:"—" }}` rzuca `VariableDoesNotExist` gdy `obj=None`.
**W Django 5.x:** Było cicho pomijane.
**Wzorzec poprawny:**
```django
{% if obj %}{{ obj.attr }}{% else %}—{% endif %}
```
**Wzorzec błędny (nie używać z nullable FK):**
```django
{{ obj.attr|default:"—" }}
```

### L4. pre-commit modyfikuje pliki — zawsze re-stage po pierwszym niepowodzeniu
**Problem:** `git commit` kończy się błędem `fix end of files — Failed`.
**Przyczyna:** Hook naprawił plik, ale zmiany są niestaged.
**Rozwiązanie:** `git add .` i ponownie `git commit` — to oczekiwane zachowanie.

### L5. Sphinx wymaga `autodoc_mock_imports` dla Django
**Problem:** `RuntimeError: Model class X doesn't declare an explicit app_label`
**Przyczyna:** `sys.path.insert(0, '../apps')` powoduje konflikt z INSTALLED_APPS.
**Rozwiązanie:**
```python
# docs/conf.py
autodoc_mock_imports = ["django", "crispy_forms", "crispy_bootstrap5",
                        "environ", "weasyprint", "openpyxl", "requests"]
# NIE dodawaj apps/ do sys.path
```

---

## 7. Szablon startowy dla nowych projektów

### 7.1 Minimalny CLAUDE.md dla nowego projektu Django

```markdown
# CLAUDE.md — Instrukcje dla projektu [NAZWA]

## Stack
- Django 6.x, Python 3.12+
- SQLite (dev), PostgreSQL (prod)
- Tabler + Bootstrap 5, django-crispy-forms
- pytest-django, black, flake8, isort, pre-commit

## Standardy
- PEP 8: PascalCase klasy, snake_case funkcje, UPPER_SNAKE_CASE stałe
- Linia max 88 znaków (Black)
- Type hints wszędzie
- Logowanie przez logging, nigdy print()
- LoginRequiredMixin na każdym widoku

## Workflow Git
- Conventional Commits: feat/fix/docs/test/chore
- Git Flow: main → develop → feature/nazwa
- Jeden commit = jedna logiczna zmiana

## Wzorce obowiązkowe
- CBV dla CRUD (ListView, CreateView, UpdateView, DeleteView)
- select_related/prefetch_related w widokach listowych
- get_queryset() z filtrowaniem per rola
- form_valid() z owner=request.user
- ActivityLog po każdej akcji CRUD
```

### 7.2 Prompt startowy dla Claude Code

```
Przeczytaj CLAUDE.md i CONTEXT.md — zaczynamy projekt [NAZWA].

Stack: Django 6.x, Python 3.14, Tabler UI, pytest-django.

Zacznij od:
1. Inicjalizacja struktury projektu (config/, apps/, templates/, static/)
2. Konfiguracja settings (base/development/production) z django-environ
3. Model bazowy: User + UserProfile z sygnałem post_save
4. Logowanie i wylogowanie (CBV + AuthenticationForm)
5. base_dashboard.html z Tablerem (sidebar, topbar, messages)
6. Pierwszy moduł CRUD: [NAZWA_MODUŁU]

Commity: Conventional Commits. Jeden commit per logiczny krok.
```

### 7.3 Checklist przed rozpoczęciem kodowania

- [ ] Zdefiniowane modele w CONTEXT.md (pola, FK, choices)
- [ ] Struktura katalogów utworzona (`django-admin startproject`)
- [ ] `.env` i `.env.example` gotowe
- [ ] `requirements/base.txt` + `development.txt` z pinned versions
- [ ] pre-commit zainstalowany (`pre-commit install`)
- [ ] Git Flow zainicjowany (`git flow init` lub ręcznie)
- [ ] CLAUDE.md z regułami projektu
- [ ] Baza danych skonfigurowana (SQLite dev, PostgreSQL prod)
- [ ] `DJANGO_SETTINGS_MODULE` w `.env`

### 7.4 Kolejność implementacji modułów (sprawdzona)

```
1. accounts (User + UserProfile + logowanie)
2. companies (pierwszy moduł CRUD — prosty)
3. contacts (FK do Company)
4. leads (lejek + WorkflowStage + Kanban)
5. tasks (powiązania do lead/deal/company)
6. deals (powiązania do lead/company)
7. documents (FileField + PDF)
8. notes (wielopowiązaniowe — najtrudniejsze FK)
9. reports (ActivityLog + XLSX — na końcu bo zbiera z poprzednich)
```

---

## 8. Co zrobić lepiej następnym razem

### Proces

| # | Ulepszenie | Uzasadnienie |
|---|-----------|--------------|
| 1 | **Zaczynać od seedowania danych** przed implementacją widoków | Bez danych testowych trudno ocenić poprawność widoków listowych |
| 2 | **Factory boy od początku** zamiast `Model.objects.create()` w testach | Mniej powtarzalnego kodu, łatwiejszy setup fixture |
| 3 | **Typowanie modeli z mypy --strict** od pierwszego commitu | Późniejsze dodanie typów do 8 000 linii to żmudna praca |
| 4 | **Mixin dla ActivityLog** zamiast ręcznego tworzenia w każdym widoku | DRY — 54 widoki × duplikacja logowania = dużo powtórzeń |
| 5 | **Jeden plik per app w urls.py** z namespace od początku | Refaktoryzacja URL w 9 aplikacjach po fakcie była czasochłonna |

### Techniczne

| # | Ulepszenie | Uzasadnienie |
|---|-----------|--------------|
| 6 | **htmx** zamiast pełnego page reload dla drobnych akcji | Kanban drag-and-drop, zmiana statusu — bez JavaScript |
| 7 | **django-allauth** zamiast custom auth views | Gotowe widoki, social login, email verification |
| 8 | **django-tables2** dla tabel listowych | Automatyczna paginacja, sortowanie, filtrowanie |
| 9 | **Celery + Redis** dla eksportu XLSX/PDF | Duże eksporty blokują wątek HTTP — warto od razu asynchronicznie |
| 10 | **PostgreSQL od początku** (nawet dev) | Różnice SQLite vs PostgreSQL ujawniają się późno (np. `distinct()`, JSON fields) |

### Dokumentacja

| # | Ulepszenie | Uzasadnienie |
|---|-----------|--------------|
| 11 | **CHANGELOG.md prowadzony na bieżąco** per commit | Retroaktywne pisanie changelogów jest uciążliwe |
| 12 | **Docstringi pisać razem z kodem**, nie na końcu | Przy 8 500 liniach retroaktywna dokumentacja to kilka dni |
| 13 | **ADR (Architecture Decision Records)** dla kluczowych decyzji | Np. "Dlaczego server-side NIP zamiast AJAX?" warto mieć utrwalone |

---

## Załączniki

### Dokumenty projektu

| Plik | Opis |
|------|------|
| [README.md](README.md) | Instalacja, uruchomienie, struktura |
| [CLAUDE.md](CLAUDE.md) | Instrukcje i standardy dla Claude Code |
| [CONTEXT.md](CONTEXT.md) | Kontekst projektu, stack, plan realizacji |
| [LESSONS_LEARNED.md](LESSONS_LEARNED.md) | 12 rozwiązanych problemów z realizacji |
| [ERD.md](ERD.md) | Diagram ERD — Mermaid (11 modeli) |
| [ERD.png](ERD.png) | Diagram ERD — obraz A3 |
| [USER_MANUAL.md](USER_MANUAL.md) | Instrukcja obsługi (13 rozdziałów) |
| [DIPLOMA_REQUIREMENTS.md](DIPLOMA_REQUIREMENTS.md) | Raport spełnienia 6 wymagań dyplomowych |
| [CHANGELOG.md](CHANGELOG.md) | Historia zmian per faza |

---

*Dokument wygenerowany: kwiecień 2026. ZelaznaCRM v1.0.*
