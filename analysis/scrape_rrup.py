"""
Skrypt analizy systemu RRUP demo.

Loguje się do https://www.uslugidemo.rrcrm.pl, przechodzi przez wszystkie
dostępne moduły i zapisuje strukturę do pliku rrup_structure.json.

Uruchomienie:
    python analysis/scrape_rrup.py

Wyniki zapisywane do: analysis/rrup_structure.json
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

# ---------------------------------------------------------------------------
# Konfiguracja
# ---------------------------------------------------------------------------
BASE_URL = "https://www.uslugidemo.rrcrm.pl"
LOGIN_URL = f"{BASE_URL}/login"
DASHBOARD_URL = f"{BASE_URL}/dashboard"
LOGIN_EMAIL = "biuro@rrup.pl"
LOGIN_PASSWORD = "rrup01012626"

OUTPUT_FILE = Path(__file__).parent / "rrup_structure.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pomocnicze funkcje ekstrakcji HTML
# ---------------------------------------------------------------------------


def extract_nav_links(soup: BeautifulSoup, base_url: str) -> list[dict[str, str]]:
    """Wyciąga linki nawigacyjne z sidebar/menu.

    Args:
        soup: Sparsowany HTML strony.
        base_url: Bazowy URL do budowania pełnych linków.

    Returns:
        Lista słowników z kluczami 'name' i 'url'.
    """
    links: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    # Szukamy w typowych miejscach nawigacji
    nav_selectors = [
        "nav a",
        ".sidebar a",
        ".navbar a",
        ".menu a",
        "[class*='nav'] a",
        "[class*='sidebar'] a",
        "[class*='menu'] a",
        "aside a",
    ]

    for selector in nav_selectors:
        for tag in soup.select(selector):
            href = tag.get("href", "")
            text = tag.get_text(strip=True)
            if not href or href in ("#", "javascript:void(0)", "javascript:;"):
                continue
            if not text or len(text) < 2:
                continue
            # Buduj pełny URL
            if href.startswith("/"):
                full_url = base_url + href
            elif href.startswith("http"):
                full_url = href
            else:
                continue
            if full_url not in seen_urls:
                seen_urls.add(full_url)
                links.append({"name": text, "url": full_url})

    return links


def extract_form_fields(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Wyciąga wszystkie pola formularzy ze strony.

    Args:
        soup: Sparsowany HTML strony.

    Returns:
        Lista słowników opisujących pola formularzy.
    """
    fields: list[dict[str, Any]] = []

    for form in soup.find_all("form"):
        form_action = form.get("action", "")
        form_method = form.get("method", "GET").upper()

        # Pola input
        for inp in form.find_all("input"):
            field_type = inp.get("type", "text")
            if field_type in ("hidden", "submit", "button", "csrf"):
                continue
            name = inp.get("name", "") or inp.get("id", "")
            if not name:
                continue
            label = _find_label(soup, inp)
            fields.append(
                {
                    "form_action": form_action,
                    "form_method": form_method,
                    "field_name": name,
                    "field_type": field_type,
                    "label": label,
                    "required": inp.has_attr("required"),
                    "placeholder": inp.get("placeholder", ""),
                    "options": [],
                }
            )

        # Pola select (listy wyboru)
        for sel in form.find_all("select"):
            name = sel.get("name", "") or sel.get("id", "")
            if not name:
                continue
            label = _find_label(soup, sel)
            options = [
                {"value": opt.get("value", ""), "text": opt.get_text(strip=True)}
                for opt in sel.find_all("option")
                if opt.get("value", "") not in ("", None)
            ]
            fields.append(
                {
                    "form_action": form_action,
                    "form_method": form_method,
                    "field_name": name,
                    "field_type": "select",
                    "label": label,
                    "required": sel.has_attr("required"),
                    "placeholder": "",
                    "options": options,
                }
            )

        # Pola textarea
        for ta in form.find_all("textarea"):
            name = ta.get("name", "") or ta.get("id", "")
            if not name:
                continue
            label = _find_label(soup, ta)
            fields.append(
                {
                    "form_action": form_action,
                    "form_method": form_method,
                    "field_name": name,
                    "field_type": "textarea",
                    "label": label,
                    "required": ta.has_attr("required"),
                    "placeholder": ta.get("placeholder", ""),
                    "options": [],
                }
            )

    return fields


def _find_label(soup: BeautifulSoup, field_tag: Any) -> str:
    """Szuka etykiety dla pola formularza.

    Args:
        soup: Sparsowany HTML strony.
        field_tag: Tag HTML pola.

    Returns:
        Tekst etykiety lub pusty string.
    """
    field_id = field_tag.get("id", "")
    if field_id:
        label_tag = soup.find("label", attrs={"for": field_id})
        if label_tag:
            return label_tag.get_text(strip=True)
    # Szukaj rodzica z klasą form-group
    parent = field_tag.parent
    for _ in range(4):
        if parent is None:
            break
        label_tag = parent.find("label")
        if label_tag:
            return label_tag.get_text(strip=True)
        parent = parent.parent
    return field_tag.get("name", "") or field_tag.get("placeholder", "")


def extract_table_columns(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Wyciąga kolumny z widoków tabelarycznych (list).

    Args:
        soup: Sparsowany HTML strony.

    Returns:
        Lista słowników z informacjami o tabelach.
    """
    tables: list[dict[str, Any]] = []

    for table in soup.find_all("table"):
        columns: list[str] = []
        thead = table.find("thead")
        if thead:
            for th in thead.find_all("th"):
                text = th.get_text(strip=True)
                if text:
                    columns.append(text)
        if columns:
            # Policz wiersze
            tbody = table.find("tbody")
            row_count = len(tbody.find_all("tr")) if tbody else 0
            tables.append(
                {
                    "columns": columns,
                    "sample_row_count": row_count,
                }
            )

    return tables


def extract_action_buttons(soup: BeautifulSoup) -> list[str]:
    """Wyciąga dostępne akcje (przyciski, filtry) ze strony.

    Args:
        soup: Sparsowany HTML strony.

    Returns:
        Lista nazw/etykiet przycisków akcji.
    """
    actions: list[str] = []
    seen: set[str] = set()

    for btn in soup.find_all(["button", "a"], attrs={"class": True}):
        classes = " ".join(btn.get("class", []))
        # Szukamy przycisków (Bootstrap/Tabler pattern)
        if any(c in classes for c in ["btn", "button", "action"]):
            text = btn.get_text(strip=True)
            if text and text not in seen and len(text) < 60:
                seen.add(text)
                actions.append(text)

    return actions[:30]  # Ogranicz do 30


# ---------------------------------------------------------------------------
# Główna logika scrapingu
# ---------------------------------------------------------------------------


def login(page: Page) -> bool:
    """Loguje się do systemu RRUP.

    Args:
        page: Obiekt strony Playwright.

    Returns:
        True jeśli logowanie powiodło się, False w przeciwnym razie.
    """
    logger.info("Przechodzę na stronę logowania: %s", LOGIN_URL)
    page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)

    # Zrzut ekranu dla diagnostyki
    page.screenshot(
        path=str(Path(__file__).parent / "screenshots" / "01_login_page.png")
    )

    soup = BeautifulSoup(page.content(), "html.parser")
    logger.info(
        "Tytuł strony logowania: %s", soup.title.string if soup.title else "brak"
    )

    # Szukamy pola email/login
    email_selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[name="login"]',
        'input[name="username"]',
        'input[id*="email"]',
        'input[id*="login"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="login" i]',
    ]
    password_selectors = [
        'input[type="password"]',
        'input[name="password"]',
        'input[name="haslo"]',
    ]

    email_field = None
    for sel in email_selectors:
        try:
            email_field = page.locator(sel).first
            if email_field.is_visible(timeout=2000):
                break
            email_field = None
        except Exception:
            email_field = None

    password_field = None
    for sel in password_selectors:
        try:
            password_field = page.locator(sel).first
            if password_field.is_visible(timeout=2000):
                break
            password_field = None
        except Exception:
            password_field = None

    if not email_field or not password_field:
        logger.error("Nie znaleziono pól logowania. Próbuję zrzut ekranu.")
        logger.info(
            "Dostępne inputy: %s",
            [
                f"name={i.get('name', '')} type={i.get('type', '')} id={i.get('id', '')}"
                for i in soup.find_all("input")
            ],
        )
        return False

    logger.info("Wypełniam formularz logowania...")
    email_field.fill(LOGIN_EMAIL)
    password_field.fill(LOGIN_PASSWORD)

    # Szukamy przycisku submit
    submit_selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Zaloguj")',
        'button:has-text("Login")',
        'button:has-text("Wejdź")',
        ".btn-primary",
    ]
    for sel in submit_selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                btn.click()
                break
        except Exception:
            continue

    # Czekamy na przekierowanie po logowaniu
    try:
        page.wait_for_url(lambda url: "login" not in url, timeout=15000)
        logger.info("Zalogowano pomyślnie! URL: %s", page.url)
    except Exception:
        # Sprawdzamy czy cokolwiek się zmieniło
        page.wait_for_load_state("networkidle", timeout=10000)
        if "login" in page.url:
            logger.error("Logowanie nie powiodło się. URL: %s", page.url)
            page.screenshot(
                path=str(Path(__file__).parent / "screenshots" / "login_failed.png")
            )
            return False

    page.screenshot(
        path=str(Path(__file__).parent / "screenshots" / "02_after_login.png")
    )
    return True


def analyze_page(page: Page, url: str, module_name: str) -> dict[str, Any]:
    """Analizuje pojedynczą stronę modułu.

    Args:
        page: Obiekt strony Playwright.
        url: URL strony do analizy.
        module_name: Nazwa modułu (dla logowania).

    Returns:
        Słownik z analizą strony.
    """
    logger.info("Analizuję: %s -> %s", module_name, url)
    try:
        page.goto(url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1500)  # Chwila na doładowanie JS
    except Exception as e:
        logger.warning("Błąd ładowania %s: %s", url, e)
        return {
            "url": url,
            "module": module_name,
            "title": "BŁĄD ŁADOWANIA",
            "error": str(e),
            "nav_links": [],
            "form_fields": [],
            "tables": [],
            "actions": [],
        }

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title else module_name

    # Sprawdź czy nie jesteśmy na stronie logowania (przekierowanie)
    if "login" in page.url:
        logger.warning("Przekierowano na logowanie dla: %s", url)
        return {
            "url": url,
            "module": module_name,
            "title": "WYMAGA LOGOWANIA",
            "nav_links": [],
            "form_fields": [],
            "tables": [],
            "actions": [],
        }

    form_fields = extract_form_fields(soup)
    tables = extract_table_columns(soup)
    actions = extract_action_buttons(soup)

    logger.info(
        "  -> Pola formularzy: %d, Tabele: %d, Akcje: %d",
        len(form_fields),
        len(tables),
        len(actions),
    )

    return {
        "url": url,
        "module": module_name,
        "title": title,
        "form_fields": form_fields,
        "tables": tables,
        "actions": actions,
    }


def discover_all_modules(page: Page) -> list[dict[str, str]]:
    """Odkrywa wszystkie moduły z nawigacji po zalogowaniu.

    Args:
        page: Obiekt strony Playwright.

    Returns:
        Lista modułów z nazwami i URL-ami.
    """
    logger.info("Odkrywam moduły z nawigacji...")
    page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(2000)

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    nav_links = extract_nav_links(soup, BASE_URL)
    logger.info("Znaleziono %d linków w nawigacji", len(nav_links))

    # Filtrujemy linki – tylko te prowadzące do rrcrm.pl i niebędące akcjami
    skip_keywords = [
        "logout",
        "wyloguj",
        "profile",
        "profil",
        "password",
        "haslo",
        "javascript",
        "#",
        "mailto",
        "tel:",
    ]
    modules: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for link in nav_links:
        url = link["url"]
        name = link["name"]
        if any(kw in url.lower() for kw in skip_keywords):
            continue
        if any(kw in name.lower() for kw in ["wyloguj", "logout", "profil"]):
            continue
        if url not in seen_urls and "rrcrm.pl" in url:
            seen_urls.add(url)
            modules.append({"name": name, "url": url})

    # Jeśli mamy mało modułów – spróbuj przez kliknięcia menu
    if len(modules) < 3:
        logger.warning("Mało modułów przez linki, próbuję kliknięcia menu...")
        modules = _discover_via_clicks(page)

    return modules


def _discover_via_clicks(page: Page) -> list[dict[str, str]]:
    """Odkrywa moduły przez klikanie elementów menu.

    Args:
        page: Obiekt strony Playwright.

    Returns:
        Lista modułów z nazwami i URL-ami.
    """
    page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=20000)
    modules: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    # Klikamy elementy menu które mogą rozwinąć podmenu
    menu_items = page.locator("nav li, .sidebar li, .menu-item").all()
    logger.info("Liczba elementów menu: %d", len(menu_items))

    for item in menu_items[:30]:
        try:
            item.click(timeout=3000)
            page.wait_for_timeout(500)
            current_url = page.url
            if current_url not in seen_urls and "login" not in current_url:
                seen_urls.add(current_url)
                text = item.inner_text().strip()
                if text and len(text) > 1:
                    modules.append({"name": text[:50], "url": current_url})
            page.go_back(wait_until="networkidle", timeout=10000)
        except Exception:
            continue

    return modules


def scrape_module_subpages(page: Page, module_url: str) -> list[str]:
    """Odkrywa podstrony modułu (np. add, edit, list).

    Args:
        page: Obiekt strony Playwright.
        module_url: URL głównej strony modułu.

    Returns:
        Lista URL podstron modułu.
    """
    try:
        page.goto(module_url, wait_until="networkidle", timeout=20000)
        page.wait_for_timeout(1000)
    except Exception:
        return []

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    subpages: list[str] = []
    seen: set[str] = set()

    # Szukamy linków do podstron (add, create, edit, show)
    keywords = [
        "add",
        "create",
        "edit",
        "new",
        "dodaj",
        "nowy",
        "nowa",
        "show",
        "detail",
    ]
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(kw in href.lower() for kw in keywords):
            if href.startswith("/"):
                full = BASE_URL + href
            elif href.startswith("http") and "rrcrm" in href:
                full = href
            else:
                continue
            if full not in seen:
                seen.add(full)
                subpages.append(full)

    return subpages[:5]  # Max 5 podstron per moduł


# ---------------------------------------------------------------------------
# Punkt wejścia
# ---------------------------------------------------------------------------


def main() -> None:
    """Główna funkcja scrapingu RRUP."""
    # Przygotuj katalogi
    screenshots_dir = Path(__file__).parent / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    result: dict[str, Any] = {
        "system": "RRUP CRM Demo",
        "base_url": BASE_URL,
        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modules": [],
        "summary": {
            "total_modules": 0,
            "total_form_fields": 0,
            "total_tables": 0,
        },
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Krok 1: Logowanie
        if not login(page):
            logger.error("Nie udało się zalogować. Sprawdź dane i URL.")
            browser.close()
            return

        # Krok 2: Odkryj moduły
        modules = discover_all_modules(page)
        logger.info("Odkryto %d modułów do analizy", len(modules))

        # Krok 3: Analizuj każdy moduł
        for mod in modules:
            page_data = analyze_page(page, mod["url"], mod["name"])

            # Zrzut ekranu
            safe_name = "".join(c for c in mod["name"] if c.isalnum() or c in " -_")[
                :30
            ]
            try:
                page.screenshot(
                    path=str(screenshots_dir / f"module_{safe_name}.png"),
                    full_page=True,
                )
            except Exception:
                pass

            # Odkryj i przeanalizuj podstrony modułu
            subpages = scrape_module_subpages(page, mod["url"])
            page_data["subpages"] = []

            for sub_url in subpages:
                sub_name = f"{mod['name']} / podstrona"
                sub_data = analyze_page(page, sub_url, sub_name)
                page_data["subpages"].append(sub_data)
                time.sleep(0.5)  # Grzeczny scraper

            result["modules"].append(page_data)
            time.sleep(1)

        browser.close()

    # Krok 4: Podsumowanie
    total_fields = sum(
        len(m.get("form_fields", []))
        + sum(len(s.get("form_fields", [])) for s in m.get("subpages", []))
        for m in result["modules"]
    )
    total_tables = sum(
        len(m.get("tables", []))
        + sum(len(s.get("tables", [])) for s in m.get("subpages", []))
        for m in result["modules"]
    )

    result["summary"] = {
        "total_modules": len(result["modules"]),
        "total_form_fields": total_fields,
        "total_tables": total_tables,
        "modules_list": [m["module"] for m in result["modules"]],
    }

    # Krok 5: Zapis do pliku
    OUTPUT_FILE.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("Wyniki zapisano do: %s", OUTPUT_FILE)
    logger.info(
        "Podsumowanie: %d modułów, %d pól formularzy, %d tabel",
        result["summary"]["total_modules"],
        result["summary"]["total_form_fields"],
        result["summary"]["total_tables"],
    )


if __name__ == "__main__":
    main()
