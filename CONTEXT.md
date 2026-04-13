# CONTEXT.md – Kontekst projektu CRM dla Claude Code

> Ten plik zawiera pełny kontekst projektu wypracowany podczas sesji planowania.
> Przeczytaj go w całości przed rozpoczęciem jakiejkolwiek pracy.

---

## 1. Cel projektu

Tworzysz **aplikację webową CRM** jako projekt dyplomowy.
Funkcjonalność projektu ma być **kopią systemu CRM firmy RRUP** (https://rrup.pl).
Masz dostęp do wersji demo RRUP pod adresem: https://www.uslugidemo.rrcrm.pl/dashboard

**Twoje pierwsze zadanie po uruchomieniu:** zalogować się do demo RRUP przy użyciu
Playwright i zebrać strukturę wszystkich modułów (formularze, pola, nawigację, URL-e).

---

## 2. Stack technologiczny

- **Framework:** Django (wzorzec MVT)
- **Język:** Python 3.12+
- **Baza danych:** PostgreSQL (produkcja), SQLite (lokalne testy)
- **Frontend:** Bootstrap 5 (via Tabler), Django Template Language, django-crispy-forms
- **UI Framework:** Tabler – https://github.com/tabler/tabler – używaj dla WSZYSTKICH stron (landing page, dashboard, formularze, tabele, Kanban)
- **Testy:** pytest-django, factory-boy, Faker (locale pl_PL), coverage
- **Narzędzia jakości:** black, flake8, isort, mypy, django-stubs, pre-commit
- **Scraping RRUP:** Playwright + beautifulsoup4
- **PDF:** weasyprint (generowanie ofert i umów z szablonów HTML)
- **Rozszerzenia Django:** django-environ, django-debug-toolbar, django-extensions, django-filter, django-guardian

---

## 3. Standardy kodowania (bezwzględnie obowiązujące)

- PEP 8: klasy `PascalCase`, funkcje/zmienne `snake_case`, stałe `UPPER_SNAKE_CASE`
- Maksymalna długość linii: 88 znaków (Black formatter)
- Type hints dla wszystkich parametrów i zwracanych wartości
- Docstringi Google Style dla każdej klasy i funkcji
- Logowanie przez `logging`, nigdy `print()`
- Konkretne wyjątki w `try/except`, nigdy gołe `except:`
- f-stringi zamiast `.format()` lub `%`
- `pathlib.Path` zamiast `os.path`

---

## 4. Architektura projektu

### Struktura katalogów
```
crm_project/
├── manage.py
├── .env                    # NIE w repozytorium
├── .env.example
├── .gitignore
├── CLAUDE.md               # Instrukcje dla AI
├── CONTEXT.md              # Ten plik
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
│   ├── accounts/           # Użytkownicy i role
│   ├── companies/          # Firmy
│   ├── contacts/           # Kontakty
│   ├── leads/              # Leady i workflow/lejek
│   ├── deals/              # Umowy/transakcje
│   ├── tasks/              # Zadania i aktywności
│   ├── documents/          # Dokumenty i PDF
│   ├── notes/              # Notatki
│   └── reports/            # Raporty i logi aktywności
├── templates/
│   ├── base.html
│   ├── components/
│   └── [app_name]/
└── static/
    ├── css/
    ├── js/
    └── img/
```

### Zasady architektoniczne
- Preferuj CBV (ListView, DetailView, CreateView, UpdateView, DeleteView) dla CRUD
- FBV tylko dla złożonej, niestandardowej logiki
- `select_related` i `prefetch_related` obowiązkowo dla widoków z relacjami
- `LoginRequiredMixin` na każdym widoku
- Wrażliwe dane WYŁĄCZNIE w `.env`

---

## 5. Modele Django – wstępna lista

### accounts
- `UserProfile` (OneToOne z User, rola: ADMIN/MANAGER/SALESPERSON/VIEWER)

### companies
- `Company` (nazwa, NIP, adres, branża, opiekun FK→User)

### contacts
- `Contact` (imię, nazwisko, firma FK→Company, email, telefon, stanowisko)

### leads
- `Lead` (tytuł, firma, kontakt, handlowiec, status, źródło, wartość, etap)
- `WorkflowStage` (nazwa etapu, kolejność, kolor Kanban)

### deals
- `Deal` (tytuł, lead FK, wartość, handlowiec, data podpisania, status)

### tasks
- `Task` (tytuł, typ, priorytet, status, termin, przypisany użytkownik, lead/deal FK)

### documents
- `Document` (tytuł, typ: OFERTA/UMOWA/PROTOKÓŁ, plik PDF, lead/deal FK)

### notes
- `Note` (treść, autor, powiązanie z lead/deal/contact)

### reports
- `ActivityLog` (użytkownik, akcja, model, object_id, opis, timestamp)

> **Ważne:** Po zebraniu danych z RRUP demo uzupełnij i rozbuduj te modele
> o dodatkowe pola które znajdziesz w formularzach systemu.

---

## 6. Workflow Git

- Strategia: **Git Flow**
- Gałęzie: `main`, `develop`, `feature/nazwa`
- Conventional Commits: `feat(modul): opis`, `fix(modul): opis`, `docs: opis`
- Atomowe commity – jedna logiczna zmiana na commit

---

## 6a. Pliki requirements – zainstaluj wszystko na starcie

### requirements/base.txt
```
Django==5.0.4
psycopg2-binary==2.9.9
django-environ==0.11.2
Pillow==10.3.0
weasyprint==62.3
django-crispy-forms==2.1
crispy-bootstrap5==2024.2
django-filter==24.1
django-guardian==2.4.0
```

### requirements/development.txt
```
-r base.txt

# Jakość kodu
black==24.3.0
flake8==7.0.0
isort==5.13.2
mypy==1.9.0
django-stubs==4.2.7
pre-commit==3.7.0

# Django narzędzia deweloperskie
django-debug-toolbar==4.3.0
django-extensions==3.2.3

# Testowanie
pytest-django==4.8.0
factory-boy==3.3.0
Faker==24.3.0
coverage==7.4.3

# Scraping RRUP (jednorazowo)
playwright==1.44.0
beautifulsoup4==4.12.3

# Narzędzia
ipython==8.23.0
rich==13.7.1
```

### requirements/production.txt
```
-r base.txt
gunicorn==21.2.0
whitenoise==6.6.0
```

### Polecenie instalacji na starcie projektu
```bash
pip install -r requirements/development.txt
playwright install chromium
pre-commit install
```

---

## 7. Plan realizacji – kolejność faz

### FAZA 1 – Analiza RRUP (zrób to jako pierwsze!)
1. Zainstaluj wszystkie zależności: `pip install -r requirements/development.txt && playwright install chromium`
2. Napisz skrypt który loguje się do https://www.uslugidemo.rrcrm.pl
3. Przejdź przez wszystkie moduły i zapisz:
   - Strukturę nawigacji i URL-e
   - Wszystkie pola formularzy (nazwa, typ, wymagalność)
   - Opcje w polach select/choice
   - Strukturę widoków listowych (kolumny)
4. Zapisz wyniki do pliku `analysis/rrup_structure.json`

### FAZA 2 – Konfiguracja środowiska
1. Inicjalizacja projektu Django ze strukturą z sekcji 4
2. Konfiguracja PostgreSQL i `.env`
3. Konfiguracja pre-commit (black, flake8, isort)
4. Inicjalizacja Git z Git Flow

### FAZA 3 – Modele
1. Implementacja modeli na podstawie analizy RRUP
2. Migracje stopniowe (po każdym modelu)
3. Rejestracja w Admin z `list_display`, `search_fields`
4. Fabryki factory-boy dla każdego modelu
5. Testy modeli

### FAZA 4 – Widoki i logika
Kolejność modułów: Accounts → Companies → Contacts → Leads → Tasks → Deals → Documents → Notes → Reports

### FAZA 5 – Szablony (Tabler jako baza dla wszystkiego)

**Konfiguracja Tabler:**
1. Pobierz Tabler z https://github.com/tabler/tabler (paczka dist/)
2. Umieść pliki CSS/JS w static/tabler/
3. Stwórz base.html dziedziczący z layoutu Tablera

**Strona startowa (landing page) – zrób jako PIERWSZĄ:**
1. Użyj komponentów Tablera: hero section, features cards, CTA button "Zaloguj się"
2. Strona ma pokazywać: nazwę systemu CRM, główne funkcje (6 kart modułów), przycisk logowania
3. Wzoruj układ na https://rrup.pl – ta sama struktura sekcji co na ich stronie głównej
4. URL: / (strona główna, dostępna bez logowania)

**Panel aplikacji (po zalogowaniu):**
1. base_dashboard.html – sidebar Tablera z menu modułów, topbar z awatarem użytkownika
2. Dziedziczenie szablonów per moduł ({% extends "base_dashboard.html" %})
3. Django messages framework dla powiadomień (alerty Tablera)
4. Tabele danych: używaj komponentów table-responsive z Tablera
5. Formularze: django-crispy-forms z layoutem Tablera
6. Kanban dla lejka sprzedażowego: użyj komponentu kanban z Tablera

### FAZA 6 – Testowanie
- pytest --cov=apps --cov-report=html (cel: min 70%)
- Testy manualne porównujące z RRUP

---

## 8. Dane do systemu RRUP demo

> Uzupełnij przed uruchomieniem skryptu Playwright:

```
URL:   https://www.uslugidemo.rrcrm.pl/login
Login: biuro@rrup.pl
Hasło: rrup01012626
```

---

## 9. Agent Skills dla Claude Code

Repozytorium skilli: https://github.com/VoltAgent/awesome-agent-skills

Skills to gotowe pliki instrukcji które Claude Code wczytuje przed konkretnym zadaniem.
Przechowuj pobrane skille w folderze `.claude/skills/` w projekcie.

### Skille użyte w projekcie

| Skill | Kiedy używać | Jak wywołać |
|-------|-------------|-------------|
| `openai/playwright-interactive` | Faza 1 – logowanie i scraping RRUP | "użyj skilla playwright-interactive" |
| `openai/frontend-skill` | Faza 5 – landing page i szablony Tabler | "użyj skilla frontend-skill" |
| `garrytan/qa` | Faza 6 – testowanie, znajdowanie bugów | "użyj skilla qa" |
| `garrytan/ship` | Po każdym module – commit, push, PR | "użyj skilla ship" |
| `garrytan/document-release` | Po każdej fazie – aktualizacja docs | "użyj skilla document-release" |

### Jak pobrać skill przed użyciem
```bash
# Utwórz folder na skille
mkdir -p .claude/skills

# Pobierz konkretny skill (przykład dla playwright-interactive)
curl -o .claude/skills/playwright-interactive.md \
  https://raw.githubusercontent.com/VoltAgent/awesome-agent-skills/main/skills/openai/playwright-interactive.md
```

---

## 10. Ważne uwagi

- To jest **projekt dyplomowy** – kod musi być zrozumiały i dobrze udokumentowany
- Przy każdym większym bloku kodu dodaj komentarz wyjaśniający co robi i dlaczego
- Używaj polskich nazw w modelach (verbose_name) i interfejsie użytkownika
- Projekt ma być **inspirowany** RRUP, nie identyczną kopią kodu – odwzorowujemy funkcjonalność
- Jeśli napotkasz na coś czego nie ma w planie – najpierw zapytaj użytkownika
