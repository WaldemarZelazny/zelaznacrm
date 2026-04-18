# Lessons Learned — ZelaznaCRM

## 1. Stary proces Django serwuje stary kod
**Problem:** Zmiany w kodzie nie są widoczne w przeglądarce.
**Przyczyna:** Na porcie 8000 działa kilka starych procesów Django.
**Rozwiązanie:**
  Windows: taskkill /F /IM python.exe
  Linux/Mac: pkill -f "manage.py runserver"
**Zapobieganie:** Zawsze zatrzymuj serwer Ctrl+C przed zamknięciem terminala.

## 2. CEIDG API v2 zostało wyłączone (1 października 2025)
**Problem:** API zwracało 404 dla każdego NIP.
**Rozwiązanie:** Zmieniono URL na v3: /api/ceidg/v3/firmy?nip={nip}
**Uwaga:** CEIDG obsługuje tylko JDG — dla spółek fallback na Białą Listę MF.

## 3. Zawsze zaczynaj sesję Claude Code od przeczytania plików MD
**Problem:** Claude Code bez kontekstu wprowadzał błędne rozwiązania
i marnował tokeny.
**Rozwiązanie:** Zawsze zaczynaj od:
  "Przeczytaj CLAUDE.md i CONTEXT.md — kontynuujemy ZelaznaCRM."

## 4. Django 6.0 zmienił obsługę None w szablonach
**Problem:** AttributeError gdy getattr(None, 'pole') — w Django 5.x
było cicho pomijane, w Django 6.0 rzuca wyjątek.
**Rozwiązanie:** Zawsze sprawdzaj {% if obiekt %} przed dostępem
do jego atrybutów w szablonach.

## 5. Sygnał post_save kontra UserProfileInline w Admin
**Problem:** IntegrityError przy tworzeniu użytkownika przez Admin —
sygnał tworzył profil automatycznie, a inline próbował go utworzyć drugi raz.
**Rozwiązanie:** extra=0 w inline + update_or_create w save_formset.

## 6. Autouzupełnianie NIP — podejście server-side lepsze niż JS
**Problem:** Rozwiązania JS/AJAX były zawodne przez cache przeglądarki
i konflikty CSS Tablera.
**Rozwiązanie:** Osobna strona /companies/nip-search/ z formularzem GET/POST
po stronie serwera — działa zawsze, niezależnie od przeglądarki.

## 7. Conventional Commits + Git Flow
**Standard:** feat(modul): opis, fix(modul): opis, docs: opis
**Gałęzie:** main → develop → feature/nazwa
**Zasada:** Jeden commit = jedna logiczna zmiana.

## 8. pre-commit hooks naprawiają pliki automatycznie
**Problem:** git commit kończy się błędem "fix end of files — Failed".
**Rozwiązanie:** Uruchom git add . && git commit ponownie —
pre-commit naprawił plik i trzeba go ponownie zacommitować.

## 9. Tokeny Claude — zarządzanie sesjami
**Problem:** Limit tokenów przerywa pracę w połowie implementacji.
**Rozwiązanie:**
- Zawsze kończ moduł przed przerwą
- Przy wznowieniu: "Sprawdź git log --oneline -5 i kontynuuj"
- Duże moduły (Leads, Tasks) zaczynaj na początku sesji

## 10. Testowanie zmian zawsze w trybie incognito
**Zasada:** Przy problemach z wyświetlaniem zawsze najpierw
sprawdź w oknie incognito (Ctrl+Shift+N) przed debugowaniem kodu.

## 11. Używane skille Claude Code
**Lokalizacja:** `.claude/skills/` — pliki `.md` z instrukcjami dla Claude Code.
**Uwaga:** Repozytorium VoltAgent/awesome-agent-skills nie zawiera plików skill
(tylko README/LICENSE) — skille zostały napisane ręcznie dla tego projektu.
`npx skills add` nie jest prawdziwą komendą — skille to zwykłe pliki Markdown.

| Skill | Plik | Kiedy używać |
|---|---|---|
| QA | `.claude/skills/garrytan-qa.md` | Przed każdym commitem nowej funkcji |
| Ship | `.claude/skills/garrytan-ship.md` | Commit + push z dobrym komunikatem |
| PDF | `.claude/skills/anthropics-pdf.md` | Generowanie dokumentów PDF (WeasyPrint) |
| XLSX | `.claude/skills/anthropics-xlsx.md` | Eksport danych do Excela (openpyxl) |

**Jak wywołać skill:**
  "Użyj skilla garrytan-qa" lub "/skill garrytan-qa"
