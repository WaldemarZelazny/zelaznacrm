# Changelog

Wszystkie istotne zmiany w projekcie ZelaznaCRM są dokumentowane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Wersjonowanie zgodne z [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-04-16

### Added

#### Infrastruktura i konfiguracja
- Projekt Django 6.0.2 z konfiguracją środowisk (base / development / test)
- Integracja z Tabler (Bootstrap 5) jako frontend framework
- Konfiguracja pre-commit hooks: black, flake8, isort
- pytest-django z osobnym plikiem konfiguracyjnym `config/settings/test.py`
- Plik `.env.example` z dokumentacją zmiennych środowiskowych

#### Moduł `accounts` — Użytkownicy i role
- Model `UserProfile` z rolami ADMIN / HANDLOWIEC (OneToOne z User)
- Sygnał auto-tworzenia profilu po rejestracji użytkownika
- Widoki: Login, Logout, Landing page, Profil
- Zarządzanie użytkownikami (ADMIN): UserListView, UserDetailView, UserCreateView, UserUpdateView
- Formularze: `UserCreateForm` (z polami profilu), `UserUpdateForm` (rola widoczna tylko dla ADMIN)

#### Moduł `companies` — Firmy
- Model `Company` z branżami (10 kategorii), NIP, danymi kontaktowymi
- Pełne CRUD: lista z filtrowaniem, szczegóły, tworzenie, edycja, usuwanie
- Filtrowanie po nazwie, branży, mieście
- Widoczność per rola: ADMIN widzi wszystkie firmy, HANDLOWIEC tylko swoje

#### Moduł `contacts` — Kontakty
- Model `Contact` powiązany z firmą, ze stanowiskiem i danymi kontaktowymi
- Pełne CRUD z dynamicznym filtrowaniem queryset FK po roli
- Filtrowanie po nazwisku i firmie

#### Moduł `leads` — Leady i lejek sprzedażowy
- Model `Lead` ze statusami (NOWY / W_TOKU / WYGRANA / PRZEGRANA / ANULOWANY)
- Model `WorkflowStage` z konfigurowalnymi etapami Kanban
- Widok tablicy Kanban z drag-and-drop (JavaScript)
- Pełne CRUD: lista, szczegóły, tworzenie, edycja, usuwanie
- Zamykanie leada z datą (`closed_at`)

#### Moduł `deals` — Umowy handlowe
- Model `Deal` z wartością, statusem (AKTYWNA / ZREALIZOWANA / ANULOWANA), datą zamknięcia
- Pełne CRUD z filtrowaniem po statusie i firmie
- Metody domenowe: `complete()`, `cancel()`

#### Moduł `tasks` — Zadania i aktywności
- Model `Task` z typami (TELEFON / EMAIL / SPOTKANIE / ZADANIE / INNE)
- Priorytety (NISKI / SREDNI / WYSOKI / PILNY) i statusy (DO_ZROBIENIA / W_TOKU / WYKONANE / ANULOWANE)
- Widok kalendarza (FullCalendar.js) z widokiem miesięcznym i tygodniowym
- Akcje: complete, cancel przez dedykowane endpointy POST
- Filtrowanie po typie, priorytecie, statusie, terminie

#### Moduł `documents` — Dokumenty
- Model `Document` z typami (OFERTA / UMOWA / PROTOKOL / FAKTURA / INNY)
- Upload plików (`FileField`) z walidacją rozszerzenia
- `DocumentDownloadView` — pobieranie przez `FileResponse` z autoryzacją
- Pełne CRUD z powiązaniami do firm, leadów, umów

#### Moduł `notes` — Notatki
- Model `Note` powiązany z firmą, leadem, umową lub kontaktem
- Pełne CRUD: autor może edytować i usuwać własne notatki; ADMIN wszystkie
- Pre-wypełnianie formularza z GET params (`company_id`, `lead_id`, `deal_id`, `contact_id`)

#### Moduł `reports` — Raporty i logi
- Model `ActivityLog` z metodą klasową `log()` do rejestrowania zdarzeń
- `ReportsDashboardView` — KPI cards + 4 wykresy Chart.js:
  - Leady per status (ostatnie 30 dni)
  - Umowy per status
  - Top 5 handlowców po wygranych leadach
  - Wartość umów per miesiąc (6 miesięcy)
- `ActivityLogListView` — lista logów z filtrowaniem po akcji, modelu, użytkowniku
- `SalesReportView` — tabela wyników per handlowiec z konwersją i wartością umów
- Wszystkie widoki dostępne tylko dla ADMIN

#### Moduł `dashboard` — Strona główna
- KPI: liczba firm, aktywnych leadów, otwartych zadań, wartość umów
- Sekcja pilnych zadań (termin dzisiaj lub przekroczony)

#### Dane demonstracyjne
- Management command `seed_demo_data` tworzący kompletny zestaw danych:
  - 2 użytkowników: `admin` (ADMIN) i `jan.kowalski` (HANDLOWIEC)
  - 10 firm z różnych branż
  - 20 kontaktów
  - 15 leadów w różnych statusach
  - 10 umów (mix statusów)
  - 20 zadań (mix typów i priorytetów)
  - 10 notatek
  - 31 logów aktywności
- Flaga `--clear` do resetowania danych

#### Testy
- 480 testów jednostkowych i integracyjnych (100% passing)
- Pokrycie: modele, widoki, formularze dla wszystkich modułów
- Testy bezpieczeństwa: uwierzytelnianie, autoryzacja per rola

---

## [Unreleased]

- Integracja z systemem RRUP (scraping Playwright)
- Generowanie PDF ofert i umów (WeasyPrint)
- API REST (Django REST Framework)
- Powiadomienia e-mail o terminach zadań
