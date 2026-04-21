# ZelaznaCRM — Instrukcja obsługi użytkownika

**Wersja:** 1.0
**Data:** Kwiecień 2026
**Autor:** Waldemar Żelazny

---

## 1. Wprowadzenie

**ZelaznaCRM** to aplikacja webowa do zarządzania relacjami z klientami (CRM), przeznaczona dla małych i średnich firm handlowych. System umożliwia zarządzanie firmami, kontaktami, leadami sprzedażowymi, umowami, zadaniami i dokumentami w jednym miejscu.

### Dla kogo jest ZelaznaCRM?

- **Handlowcy** — prowadzenie lejka sprzedażowego, zarządzanie zadaniami i kontaktami
- **Menedżerowie sprzedaży** — monitorowanie zespołu, raporty, statystyki KPI
- **Administratorzy** — zarządzanie użytkownikami i uprawnieniami systemu

### Główne funkcje

- Zarządzanie firmami i kontaktami
- Lejek sprzedażowy z widokiem Kanban
- Umowy i dokumenty (generowanie PDF)
- Zadania z kalendarzem
- Notatki powiązane z obiektami CRM
- Raporty i eksport do Excela
- Logi aktywności użytkowników

---

## 2. Pierwsze kroki

### 2.1 Logowanie

1. Otwórz przeglądarkę i przejdź pod adres systemu
2. Na stronie głównej kliknij przycisk **„Zaloguj się"**
3. Wprowadź nazwę użytkownika i hasło
4. Kliknij **„Zaloguj"**

Po poprawnym zalogowaniu zostaniesz przekierowany do pulpitu (dashboard).

### 2.2 Role użytkowników

System obsługuje dwie role:

| Rola | Uprawnienia |
|------|-------------|
| **ADMIN** | Pełny dostęp — widzi wszystkie rekordy wszystkich użytkowników, może tworzyć i usuwać użytkowników |
| **HANDLOWIEC** | Widzi tylko swoje rekordy (firmy, leady, umowy, zadania, kontakty) |

### 2.3 Wylogowanie

Kliknij ikonę użytkownika w prawym górnym rogu → **„Wyloguj"**.

---

## 3. Dashboard

Pulpit główny wyświetla kluczowe wskaźniki KPI po zalogowaniu.

### Widżety na pulpicie

| Wskaźnik | Opis |
|----------|------|
| **Aktywne leady** | Liczba leadów o statusie „Nowy" lub „W toku" |
| **Umowy w tym miesiącu** | Liczba umów utworzonych w bieżącym miesiącu |
| **Zadania na dziś** | Liczba zadań z terminem na dzisiaj |
| **Przeterminowane zadania** | Liczba niezrealizowanych zadań po terminie |
| **Wartość aktywnych umów** | Suma wartości umów ze statusem „Aktywna" |
| **Zadania w toku** | Liczba zadań o statusie „W toku" |

Dashboard automatycznie filtruje dane według roli — HANDLOWIEC widzi tylko swoje statystyki.

---

## 4. Firmy

Moduł **Firmy** służy do zarządzania danymi firm-klientów i potencjalnych klientów.

### 4.1 Lista firm

Przejdź do menu **Firmy → Lista firm**.

Dostępne filtry:
- **Nazwa** — wyszukiwanie po fragmentem nazwy
- **Miasto** — filtrowanie po miejscowości
- **Branża** — wybór z listy branż

### 4.2 Dodawanie firmy

1. Kliknij **„Dodaj firmę"**
2. Wypełnij formularz (pola obowiązkowe: **Nazwa**)
3. Opcjonalnie skorzystaj z **Wyszukiwarki NIP** (patrz rozdział 13)
4. Kliknij **„Zapisz"**

#### Pola formularza firmy

| Pole | Opis | Wymagane |
|------|------|----------|
| Nazwa | Pełna nazwa firmy | Tak |
| NIP | Numer identyfikacji podatkowej | Nie |
| Adres | Ulica i numer | Nie |
| Miasto | Miejscowość | Nie |
| Kod pocztowy | Kod pocztowy | Nie |
| Telefon | Numer telefonu | Nie |
| Email | Adres e-mail | Nie |
| Strona WWW | Adres strony internetowej | Nie |
| Branża | Wybór z listy | Nie |
| Notatki | Dowolny tekst | Nie |

### 4.3 Edycja firmy

Na stronie szczegółów firmy kliknij **„Edytuj"**. Edycja dostępna dla właściciela rekordu lub ADMIN.

### 4.4 Usuwanie firmy

Tylko ADMIN może usunąć firmę. Usunięcie firmy usuwa też powiązane leady (CASCADE).

---

## 5. Kontakty

Moduł **Kontakty** przechowuje dane osób kontaktowych powiązanych z firmami.

### 5.1 Lista kontaktów

Filtry: **Imię/Nazwisko**, **Firma**, **Dział**.

### 5.2 Dodawanie kontaktu

1. Kliknij **„Dodaj kontakt"**
2. Wybierz firmę z listy
3. Podaj dane osoby: imię, nazwisko, stanowisko
4. Kliknij **„Zapisz"**

#### Pola formularza kontaktu

| Pole | Opis | Wymagane |
|------|------|----------|
| Imię | Imię osoby | Tak |
| Nazwisko | Nazwisko osoby | Tak |
| Firma | Powiązana firma | Tak |
| Email | Adres e-mail | Nie |
| Telefon | Numer telefonu | Nie |
| Stanowisko | Stanowisko w firmie | Nie |
| Dział | Dział organizacyjny | Nie |
| Notatki | Dowolne uwagi | Nie |

---

## 6. Leady

Moduł **Leady** obsługuje lejek sprzedażowy — od pierwszego kontaktu do wygranej lub przegranej.

### 6.1 Statusy leada

| Status | Znaczenie |
|--------|-----------|
| **Nowy** | Lead właśnie dodany, bez działań |
| **W toku** | Trwają rozmowy sprzedażowe |
| **Wygrana** | Transakcja zakończona sukcesem |
| **Przegrana** | Klient nie zdecydował się na zakup |
| **Anulowany** | Lead wycofany z lejka |

### 6.2 Widok listy leadów

Filtry: **Status**, **Źródło**, **Etap Kanban**.

### 6.3 Widok Kanban

Przejdź do **Leady → Kanban**. Leady wyświetlane są w kolumnach odpowiadających etapom lejka (Nowy, Kontakt, Oferta, Negocjacje, Wygrana, Przegrana).

Etapy Kanban konfiguruje ADMIN w panelu administracyjnym.

### 6.4 Zmiana statusu leada

Na stronie szczegółów leada dostępne są przyciski:
- **„Zamknij jako wygraną"** — ustawia status WYGRANA i zapisuje datę zamknięcia
- **„Zamknij jako przegraną"** — ustawia status PRZEGRANA
- **„Anuluj"** — ustawia status ANULOWANY

### 6.5 Źródła leadów

| Źródło | Znaczenie |
|--------|-----------|
| Formularz www | Lead z formularza na stronie |
| Polecenie | Od obecnego klienta lub partnera |
| Cold call | Proaktywny kontakt telefoniczny |
| Kampania marketingowa | Z działań marketingowych |
| Targi / Wydarzenie | Ze spotkania branżowego |
| Inne | Inne źródło |

---

## 7. Umowy

Moduł **Umowy** zarządza transakcjami handlowymi i kontraktami.

### 7.1 Statusy umowy

| Status | Znaczenie |
|--------|-----------|
| **Aktywna** | Umowa w trakcie realizacji |
| **Zrealizowana** | Umowa wykonana, podpisana |
| **Anulowana** | Umowa anulowana |

### 7.2 Tworzenie umowy

1. Przejdź do **Umowy → Nowa umowa**
2. Podaj tytuł umowy i wybierz firmę
3. Opcjonalnie powiąż z istniejącym leadem
4. Ustaw wartość, termin realizacji i opis
5. Kliknij **„Zapisz"**

### 7.3 Akcje na umowie

Na stronie szczegółów umowy:
- **„Oznacz jako zrealizowaną"** — ustawia status ZREALIZOWANA, zapisuje datę podpisania
- **„Anuluj umowę"** — ustawia status ANULOWANA (tylko dla umów aktywnych)

### 7.4 Eksport do Excela

Na liście umów kliknij **„Eksportuj do Excel"** — pobierasz plik `.xlsx` z przefiltrowanymi umowami.

---

## 8. Zadania

Moduł **Zadania** służy do planowania i śledzenia aktywności handlowych.

### 8.1 Typy zadań

| Typ | Użycie |
|-----|--------|
| **Telefon** | Zaplanowana rozmowa telefoniczna |
| **E-mail** | Korespondencja e-mailowa |
| **Spotkanie** | Spotkanie z klientem |
| **Zadanie** | Ogólne zadanie do wykonania |
| **Inne** | Inne aktywności |

### 8.2 Priorytety

| Priorytet | Kolor w kalendarzu |
|-----------|-------------------|
| **Niski** | Szary |
| **Średni** | Niebieski |
| **Wysoki** | Pomarańczowy |
| **Pilny** | Czerwony |

### 8.3 Statusy zadania

| Status | Znaczenie |
|--------|-----------|
| **Do zrobienia** | Zadanie zaplanowane |
| **W toku** | Zadanie w realizacji |
| **Wykonane** | Zadanie ukończone |
| **Anulowane** | Zadanie anulowane |

### 8.4 Widok kalendarza

Przejdź do **Zadania → Kalendarz**. Zadania wyświetlane są na interaktywnym kalendarzu (FullCalendar). Kliknij zadanie aby przejść do jego szczegółów.

### 8.5 Oznaczanie zadania jako wykonane

Na stronie szczegółów zadania kliknij **„Oznacz jako wykonane"**. System automatycznie zapisuje datę i godzinę wykonania.

---

## 9. Dokumenty

Moduł **Dokumenty** umożliwia przechowywanie plików i generowanie dokumentów PDF.

### 9.1 Typy dokumentów

| Typ | Opis |
|-----|------|
| **Oferta** | Oferta handlowa dla klienta |
| **Umowa** | Dokument umowy |
| **Protokół** | Protokół odbioru lub spotkania |
| **Faktura** | Dokument fakturowy |
| **Inne** | Inne dokumenty |

### 9.2 Wgrywanie dokumentu

1. Przejdź do **Dokumenty → Wgraj dokument**
2. Podaj tytuł i wybierz typ dokumentu
3. Powiąż z firmą, leadem lub umową
4. Kliknij **„Wybierz plik"** i wskaż plik na dysku
5. Kliknij **„Zapisz"**

Obsługiwane formaty plików: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG.

### 9.3 Generowanie PDF

Na stronie szczegółów dokumentu (typ: Oferta lub Umowa) kliknij **„Generuj PDF"**. System tworzy profesjonalny dokument PDF na podstawie danych z CRM.

---

## 10. Notatki

Moduł **Notatki** pozwala dodawać krótkie wpisy tekstowe powiązane z obiektami CRM.

### 10.1 Dodawanie notatki

Notatki można dodawać z poziomu:
- Strony szczegółów **firmy**
- Strony szczegółów **leada**
- Strony szczegółów **umowy**
- Strony szczegółów **kontaktu**
- Modułu **Notatki → Dodaj notatkę** (z ręcznym wyborem powiązania)

### 10.2 Powiązania notatki

Notatka może być powiązana jednocześnie z:
- Firmą
- Leadem
- Umową
- Kontaktem

Przy wyświetlaniu priorytety: Umowa > Lead > Firma > Kontakt.

### 10.3 Edycja i usuwanie

Notatkę może edytować tylko jej **autor** lub **ADMIN**.

---

## 11. Raporty

Moduł **Raporty** dostarcza statystyki i wizualizacje danych — dostępny tylko dla ADMIN.

### 11.1 Raport sprzedaży

Przejdź do **Raporty → Raport sprzedaży**.

Wyświetlane dane:
- Wykresy: leady wg statusu, umowy wg miesiąca, wartość pipeline
- Tabele: top handlowcy, najlepsze miesiące
- Filtrowanie po zakresie dat

### 11.2 Eksport do Excela

Na stronie raportu kliknij **„Eksportuj do Excel"** — pobierasz szczegółowy raport `.xlsx`.

### 11.3 Logi aktywności

Przejdź do **Raporty → Logi aktywności**.

Każda akcja użytkownika (utworzenie, edycja, usunięcie, wyświetlenie) jest rejestrowana z:
- Użytkownikiem wykonującym akcję
- Typem akcji i modelem
- Datą i godziną zdarzenia
- Adresem IP

Filtry: **Akcja**, **Nazwa modelu**, **Użytkownik**.

---

## 12. Administracja

Panel administracyjny dostępny wyłącznie dla użytkowników z rolą **ADMIN**.

### 12.1 Zarządzanie użytkownikami

Przejdź do **Administracja → Użytkownicy**.

Lista wyświetla wszystkich użytkowników z kolumnami: imię i nazwisko, login, rola, data ostatniego logowania.

### 12.2 Tworzenie nowego użytkownika

1. Kliknij **„Dodaj użytkownika"**
2. Wypełnij pola: **nazwa użytkownika**, **hasło**, imię, nazwisko, e-mail
3. Wybierz **rolę**: ADMIN lub HANDLOWIEC
4. Opcjonalnie podaj numer telefonu
5. Kliknij **„Zapisz"**

### 12.3 Edycja użytkownika

ADMIN może edytować dane każdego użytkownika. Handlowiec może edytować tylko swój własny profil.

### 12.4 Panel Django Admin

Zaawansowane operacje administracyjne (edycja etapów Kanban, importy danych) dostępne pod adresem `/admin/` (tylko dla superużytkowników).

---

## 13. Wyszukiwarka NIP

Przy dodawaniu lub edycji firmy dostępna jest funkcja automatycznego uzupełniania danych na podstawie NIP.

### 13.1 Jak używać

1. W formularzu firmy kliknij **„Szukaj po NIP"** lub przejdź do `/companies/nip-search/`
2. Wpisz 10-cyfrowy NIP (bez myślników)
3. Kliknij **„Szukaj"**
4. System pobiera dane z rejestru CEIDG lub Białej Listy MF
5. Formularz zostaje wstępnie wypełniony danymi firmy
6. Sprawdź poprawność danych i kliknij **„Zapisz"**

### 13.2 Źródła danych

| Źródło | Typ firm | Dostępność |
|--------|----------|------------|
| **CEIDG** (dane.biznes.gov.pl) | Jednoosobowe działalności gospodarcze (JDG) | Wymaga tokenu API |
| **Biała Lista MF** (wl-api.mf.gov.pl) | Spółki i inne podmioty | Bezpłatne, bez tokenu |

### 13.3 Możliwe komunikaty błędów

| Komunikat | Przyczyna |
|-----------|-----------|
| „NIP nie znaleziony" | Brak firmy w rejestrze lub błędny NIP |
| „Nieprawidłowy NIP — błąd sumy kontrolnej" | Podany numer nie przeszedł walidacji algorytmem NIP |
| „Błąd połączenia z rejestrem" | Tymczasowy brak dostępu do zewnętrznego API |

---

*Dokument wygenerowany dla ZelaznaCRM v1.0 — projekt dyplomowy, kwiecień 2026.*
