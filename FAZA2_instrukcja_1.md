# Instrukcja dla Claude Code – Faza 2 i dalej
# CRM dla małego zespołu (max 5 handlowców)
# Na podstawie analizy rrup_structure.json (48 modułów, 228 pól, 78 tabel)

---

## ZAKRES PROJEKTU – OSTATECZNA DECYZJA

### ✅ IMPLEMENTUJ – Core CRM (obowiązkowe)
1. **Dashboard** – panel główny ze statystykami sprzedaży
2. **Klienci** – lista, szczegóły, dodawanie, edycja (/customer)
3. **Oferty** – tworzenie, lista, statusy (/offers)
4. **Umowy** – lista, szczegóły, monitor (/agreements)
5. **Zadania** – lista zadań + kalendarz (/tasks, /tasks-calendar)
6. **Użytkownicy** – tylko Admin i Handlowcy (max 5), role (/admin, /trader, /roles)
7. **Raporty** – statystyki sprzedaży, raporty handlowe (/stats, /trader_reports)
8. **Ustawienia** – dane własne, konfiguracja (/settings)
9. **Notatki** – notatki przy klientach i umowach

### ⚠️ IMPLEMENTUJ UPROSZCZONE
10. **Kampanie** – tylko lista i tworzenie (/modules/campaign)
11. **Reklamacje** – podstawowy CRUD (/modules/complaints)
12. **Projekty** – podstawowy CRUD (/projects)
13. **Faktury** – tylko lista (/business/invoices)

### ❌ POMIŃ – usunięte na życzenie lub zbyt złożone
- Oddziały (/agent) – niepotrzebne dla małego zespołu
- Monterzy (/monter) – nie dotyczy
- Magazynierzy (/warehouseman) – nie dotyczy
- Moduł magazynowy (/warehouse/*) – nie dotyczy
- Prowizje (/users-commissions) – nie dotyczy
- Struktura drzewa (/users-structure-tree) – nie dotyczy
- Moderatorzy (/moderator) – nie dotyczy
- Formularze Facebook (/facebook_lead_items) – wymaga API
- Formularze dedykowane (/external-forms) – zbyt złożone
- Kalkulator ofertowy (/super-calculator) – zbyt złożony
- Panel telemarketera (/telemarketer-panel) – nie dotyczy
- Płatności RRUP (/rrup/*) – nie dotyczy

---

## ROLE UŻYTKOWNIKÓW (uproszczone)

| Rola | Opis | Uprawnienia |
|------|------|-------------|
| ADMIN | Administrator systemu | Pełny dostęp, zarządzanie użytkownikami |
| HANDLOWIEC | Sprzedawca (max 5 osób) | Własni klienci, oferty, zadania, raporty |

---

## PROMPT DLA CLAUDE CODE – FAZA 2

Wklej poniższy tekst do Claude Code:

```
Faza 1 zakończona. Analiza RRUP wykonana (rrup_structure.json).

Projekt ZelaznaCRM to uproszczony CRM dla małego zespołu max 5 handlowców.
Role: tylko ADMIN i HANDLOWIEC. Bez modułów: magazyn, prowizje, oddziały,
monterzy, magazynierzy, moderatorzy, telemarketer.

Rozpocznij FAZĘ 2 – Konfiguracja środowiska:

1. Zainicjalizuj projekt Django o nazwie "config" ze strukturą zgodną
   z CLAUDE.md sekcja 7 (Struktura Projektu) w bieżącym katalogu ZelaznaCRM.

2. Stwórz pliki requirements zgodnie z CONTEXT.md sekcja 6a:
   - requirements/base.txt
   - requirements/development.txt
   - requirements/production.txt

3. Stwórz konfigurację Django:
   - config/settings/base.py
   - config/settings/development.py (DEBUG=True, SQLite)
   - config/settings/production.py (DEBUG=False, PostgreSQL)

4. Stwórz plik .env i .env.example:
   SECRET_KEY, DATABASE_URL, DEBUG, ALLOWED_HOSTS

5. Zainicjalizuj Git:
   - git init
   - stwórz gałęzie main i develop
   - .gitignore dla Python/Django
   - pierwszy commit: "chore: initialize ZelaznaCRM project structure"

6. Zainstaluj i skonfiguruj pre-commit (black, flake8, isort)
   zgodnie z CLAUDE.md sekcja 8.

7. Utwórz puste aplikacje Django (w folderze apps/):
   - accounts   (użytkownicy i role: ADMIN, HANDLOWIEC)
   - companies  (firmy/klienci)
   - contacts   (osoby kontaktowe)
   - leads      (leady i lejek sprzedażowy)
   - deals      (umowy i transakcje)
   - tasks      (zadania i kalendarz)
   - documents  (dokumenty i PDF)
   - notes      (notatki)
   - reports    (raporty i logi)

8. Zainstaluj zależności:
   pip install -r requirements/development.txt

9. Wykonaj pierwszą migrację i sprawdź że serwer działa:
   python manage.py migrate
   python manage.py runserver

Po zakończeniu:
- Pokaż drzewo struktury katalogów projektu
- Potwierdź że serwer uruchamia się bez błędów
- Zrób commit: "chore: add Django apps scaffold"

Czekaj na moje zatwierdzenie przed przejściem do Fazy 3 (modele).
```

---

## CO DALEJ – FAZA 3 (Modele Django)

Kolejność tworzenia modeli (od najmniej do najbardziej zależnych):

### 1. accounts/models.py
```
UserProfile (OneToOne z User)
- role: CharField(choices) → ADMIN / HANDLOWIEC
- phone: CharField
- avatar: ImageField (opcjonalne)
- created_at: DateTimeField(auto_now_add)
```

### 2. companies/models.py
```
Company
- name: CharField (nazwa firmy lub klienta indywidualnego)
- nip: CharField(unique, blank=True)
- address: TextField
- city: CharField
- phone: CharField
- email: EmailField
- website: URLField (opcjonalne)
- owner: ForeignKey(User) – opiekun handlowy
- created_at: DateTimeField(auto_now_add)
```

### 3. contacts/models.py
```
Contact
- first_name, last_name: CharField
- company: ForeignKey(Company)
- email: EmailField
- phone: CharField
- position: CharField (stanowisko)
- owner: ForeignKey(User)
- created_at: DateTimeField(auto_now_add)
```

### 4. leads/models.py
```
WorkflowStage
- name: CharField (np. Nowy, Kontakt, Oferta, Negocjacje, Wygrana, Przegrana)
- order: PositiveIntegerField
- color: CharField (kolor hex dla Kanbana)

Lead
- title: CharField
- company: ForeignKey(Company)
- contact: ForeignKey(Contact, null=True)
- owner: ForeignKey(User)
- status: CharField(choices) → NOWY/W_TOKU/WYGRANA/PRZEGRANA/ANULOWANY
- source: CharField(choices) → FORMULARZ/POLECENIE/COLD_CALL/KAMPANIA/INNE
- value: DecimalField (szacowana wartość PLN)
- stage: ForeignKey(WorkflowStage)
- created_at: DateTimeField(auto_now_add)
- closed_at: DateTimeField(null=True)
```

### 5. deals/models.py
```
Deal
- title: CharField
- lead: ForeignKey(Lead, null=True)
- company: ForeignKey(Company)
- value: DecimalField
- owner: ForeignKey(User)
- status: CharField(choices) → AKTYWNA/ZREALIZOWANA/ANULOWANA
- signed_at: DateField(null=True)
- close_date: DateField
- created_at: DateTimeField(auto_now_add)
```

### 6. tasks/models.py
```
Task
- title: CharField
- description: TextField(blank=True)
- task_type: CharField(choices) → TELEFON/EMAIL/SPOTKANIE/INNE
- priority: CharField(choices) → NISKI/SREDNI/WYSOKI/PILNY
- status: CharField(choices) → DO_ZROBIENIA/W_TOKU/WYKONANE
- due_date: DateTimeField
- assigned_to: ForeignKey(User)
- lead: ForeignKey(Lead, null=True)
- deal: ForeignKey(Deal, null=True)
- company: ForeignKey(Company, null=True)
- created_by: ForeignKey(User)
- created_at: DateTimeField(auto_now_add)
```

### 7. documents/models.py
```
Document
- title: CharField
- doc_type: CharField(choices) → OFERTA/UMOWA/PROTOKOL/INNY
- lead: ForeignKey(Lead, null=True)
- deal: ForeignKey(Deal, null=True)
- file: FileField
- created_by: ForeignKey(User)
- created_at: DateTimeField(auto_now_add)
```

### 8. notes/models.py
```
Note
- content: TextField
- lead: ForeignKey(Lead, null=True)
- deal: ForeignKey(Deal, null=True)
- company: ForeignKey(Company, null=True)
- author: ForeignKey(User)
- created_at: DateTimeField(auto_now_add)
```

### 9. reports/models.py
```
ActivityLog
- user: ForeignKey(User)
- action: CharField(choices) → CREATED/UPDATED/DELETED/VIEWED
- model_name: CharField
- object_id: PositiveIntegerField
- description: TextField
- created_at: DateTimeField(auto_now_add)
```

---

## PROMPT DLA CLAUDE CODE – FAZA 3

Po zatwierdzeniu Fazy 2 wklej:

```
Faza 2 zatwierdzona. Środowisko skonfigurowane.

Rozpocznij FAZĘ 3 – Modele Django.

Zaimplementuj modele zgodnie z listą w pliku FAZA2_instrukcja.md sekcja
"CO DALEJ – FAZA 3". Twórz modele w tej kolejności:
accounts → companies → contacts → leads → deals → tasks → documents → notes → reports

Dla każdego modelu:
1. Napisz model z pełnymi type hints i docstringami (Google Style)
2. Wykonaj makemigrations i migrate
3. Zarejestruj w admin.py z list_display i search_fields
4. Napisz fabrykę factory-boy
5. Napisz podstawowe testy modelu
6. Zrób commit: "feat(nazwa_modulu): add model"

Używaj polskich verbose_name w modelach.
Używaj IntegerChoices lub TextChoices dla pól wyboru.

Czekaj na moje zatwierdzenie po każdym module przed przejściem do następnego.
```
