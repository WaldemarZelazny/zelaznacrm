"""Management command: seed_demo_data.

Tworzy kompletny zestaw danych demonstracyjnych dla ZelaznaCRM:
  - 2 uzytkownikow (admin + handlowiec)
  - 10 firm z roznych branzy
  - 20 kontaktow przypisanych do firm
  - 15 leadow w roznych etapach lejka
  - 10 umow (mix statusow)
  - 20 zadan (mix typow i priorytetow)
  - 10 notatek
  - Logi aktywnosci dla wszystkich powyzszych

Uzycie:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --clear   # usuwa dane przed seedowaniem
"""

from __future__ import annotations

import datetime
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.deals.models import Deal
from apps.leads.models import Lead, WorkflowStage
from apps.notes.models import Note
from apps.reports.models import ActivityLog
from apps.tasks.models import Task

# ---------------------------------------------------------------------------
# Stale danych testowych
# ---------------------------------------------------------------------------

COMPANIES = [
    ("Techsfera Sp. z o.o.", "IT", "IT / Technologia", "22-100-22-00", "techsfera.pl"),
    ("BudMax S.A.", "BUDOWNICTWO", "Budownictwo", "12-200-12-00", "budmax.pl"),
    ("HandelPro Sp. z o.o.", "HANDEL", "Handel", "33-300-33-00", "handelpro.pl"),
    ("MetalWork Sp. z o.o.", "PRODUKCJA", "Produkcja", "44-400-44-00", "metalwork.pl"),
    ("QuickServ S.A.", "USLUGI", "Uslugi", "55-500-55-00", "quickserv.pl"),
    ("FinTrust S.A.", "FINANSE", "Finanse", "66-600-66-00", "fintrust.pl"),
    ("LogiTrans Sp. z o.o.", "TRANSPORT", "Transport", "77-700-77-00", "logitrans.pl"),
    ("MediCare Sp. z o.o.", "ZDROWIE", "Zdrowie", "88-800-88-00", "medicare.pl"),
    ("EduPlus Sp. z o.o.", "EDUKACJA", "Edukacja", "99-900-99-00", "eduplus.pl"),
    ("OmniGroup S.A.", "INNE", "Inne", "11-111-11-11", "omnigroup.pl"),
]

CONTACTS = [
    ("Anna", "Kowalska", "Dyrektor sprzedazy", "anna.kowalska@example.com"),
    ("Marek", "Nowak", "Kierownik projektu", "marek.nowak@example.com"),
    ("Joanna", "Wisniowska", "Prezes", "joanna.wisniowska@example.com"),
    ("Tomasz", "Zielinski", "Specjalista ds. zakupow", "tomasz.zielinski@example.com"),
    ("Katarzyna", "Lewandowska", "CFO", "katarzyna.lewandowska@example.com"),
    ("Piotr", "Wojciechowski", "CTO", "piotr.wojciechowski@example.com"),
    ("Monika", "Kaminska", "Menedzer ds. relacji", "monika.kaminska@example.com"),
    ("Lukasz", "Krawczyk", "Dyrektor operacyjny", "lukasz.krawczyk@example.com"),
    ("Magdalena", "Jankowska", "Specjalista IT", "magdalena.jankowska@example.com"),
    ("Robert", "Wisniak", "Kierownik sprzedazy", "robert.wisniak@example.com"),
    ("Agnieszka", "Dabrowska", "Analityk biznesowy", "agnieszka.dabrowska@example.com"),
    ("Michal", "Mazur", "Dyrektor generalny", "michal.mazur@example.com"),
    ("Ewa", "Pawlak", "HR Manager", "ewa.pawlak@example.com"),
    (
        "Bartosz",
        "Michalski",
        "Specjalista ds. marketingu",
        "bartosz.michalski@example.com",
    ),
    ("Natalia", "Adamczyk", "Project Manager", "natalia.adamczyk@example.com"),
    ("Krzysztof", "Dudek", "Dyrektor finansowy", "krzysztof.dudek@example.com"),
    ("Sylwia", "Wieczorek", "Konsultant", "sylwia.wieczorek@example.com"),
    ("Adam", "Jakubowski", "Technolog", "adam.jakubowski@example.com"),
    ("Beata", "Szymanska", "Koordynator projektow", "beata.szymanska@example.com"),
    ("Marcin", "Walczak", "Account Manager", "marcin.walczak@example.com"),
]

LEAD_TITLES = [
    "Wdrozenie systemu ERP",
    "Modernizacja infrastruktury IT",
    "Dostawa materialow budowlanych Q2",
    "Kontrakt na usluge logistyczna",
    "Projekt automatyzacji produkcji",
    "Ubezpieczenie floty pojazdow",
    "Szkolenia dla pracownikow",
    "Konsultacje prawne – umowy handlowe",
    "Dostawa sprzetu medycznego",
    "Platforma e-learningowa",
    "Outsourcing obslugi IT",
    "Kontrakt serwisowy 24/7",
    "Projekt transformacji cyfrowej",
    "Kampania reklamowa Q3",
    "Wdrozenie CRM",
]

DEAL_TITLES = [
    "Umowa na wdrozenie ERP – Techsfera",
    "Kontrakt budowlany – BudMax",
    "Umowa dostawy – HandelPro",
    "Projekt automatyzacji – MetalWork",
    "Kontrakt serwisowy – QuickServ",
    "Ubezpieczenie mienia – FinTrust",
    "Umowa transportowa – LogiTrans",
    "Dostawa sprzetu – MediCare",
    "Licencja platformy – EduPlus",
    "Umowa ramowa – OmniGroup",
]

NOTE_CONTENTS = [
    "Klient zainteresowany rozszerzeniem wspolpracy w Q4. Omowic oferte na dodatkowe uslugi.",
    "Spotkanie odbylo sie zgodnie z planem. Klient prosi o szczegolowa wycene do konca tygodnia.",
    "Kontakt potwierdzil zainteresowanie. Kolejny krok: prezentacja produktu.",
    "Reklamacja zlozona przez klienta – przekazac do dzialu technicznego.",
    "Klient planuje rozbudowe dzialu – potencjal na nowy lead w Q1.",
    "Umowa podpisana. Przekazac do realizacji. Termin startowy: 1. przyszlego miesiaca.",
    "Negocjacje w toku. Klient oczekuje rabatu 10% przy zamowieniu rocznym.",
    "Follow-up po targach. Klient pamietany z poprzedniej wspolpracy – priorytet.",
    "Wyslano oferte handlowa. Oczekiwanie na odpowiedz – termin do piatku.",
    "Klient wymaga dodatkowej dokumentacji technicznej. Przygotowac i wyslac.",
]


class Command(BaseCommand):
    """Seeduje baze danych danymi demonstracyjnymi."""

    help = "Tworzy dane demonstracyjne dla ZelaznaCRM"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Usuwa istniejace dane przed seedowaniem (oprocz superuserow)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_data()

        self.stdout.write("Seedowanie danych demonstracyjnych...")

        admin, handlowiec = self._create_users()
        companies = self._create_companies(admin, handlowiec)
        contacts = self._create_contacts(companies)
        stages = self._ensure_workflow_stages()
        leads = self._create_leads(companies, contacts, handlowiec, stages)
        deals = self._create_deals(companies, leads, handlowiec)
        self._create_tasks(companies, leads, deals, admin, handlowiec)
        self._create_notes(companies, leads, deals, contacts, handlowiec)
        self._create_activity_logs(admin, handlowiec, companies, leads, deals)

        self.stdout.write(self.style.SUCCESS("Seedowanie zakonczone pomyslnie!"))
        self.stdout.write("")
        self.stdout.write("Dane logowania:")
        self.stdout.write("  admin      / Admin1234!")
        self.stdout.write("  jan.kowalski / Handlowiec1!")

    # ------------------------------------------------------------------
    # Czyszczenie danych
    # ------------------------------------------------------------------

    def _clear_data(self):
        self.stdout.write("Czyszczenie istniejacych danych...")
        ActivityLog.objects.all().delete()
        Note.objects.all().delete()
        Task.objects.all().delete()
        Deal.objects.all().delete()
        Lead.objects.all().delete()
        Contact.objects.all().delete()
        Company.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("  Usunieto istniejace rekordy.")

    # ------------------------------------------------------------------
    # Uzytkownicy
    # ------------------------------------------------------------------

    def _create_users(self):
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Adam",
                "last_name": "Administrator",
                "email": "admin@zelaznacrm.pl",
                "is_staff": True,
            },
        )
        if created:
            admin.set_password("Admin1234!")
            admin.save()
            admin.profile.role = UserProfile.Role.ADMIN
            admin.profile.phone = "500-100-200"
            admin.profile.save()
            self.stdout.write(f"  Utworzono: {admin.username} (ADMIN)")
        else:
            self.stdout.write(f"  Istnieje: {admin.username}")

        handlowiec, created = User.objects.get_or_create(
            username="jan.kowalski",
            defaults={
                "first_name": "Jan",
                "last_name": "Kowalski",
                "email": "jan.kowalski@zelaznacrm.pl",
            },
        )
        if created:
            handlowiec.set_password("Handlowiec1!")
            handlowiec.save()
            handlowiec.profile.role = UserProfile.Role.HANDLOWIEC
            handlowiec.profile.phone = "500-300-400"
            handlowiec.profile.save()
            self.stdout.write(f"  Utworzono: {handlowiec.username} (HANDLOWIEC)")
        else:
            self.stdout.write(f"  Istnieje: {handlowiec.username}")

        return admin, handlowiec

    # ------------------------------------------------------------------
    # Firmy
    # ------------------------------------------------------------------

    def _create_companies(self, admin, handlowiec):
        companies = []
        owners = [
            admin,
            handlowiec,
            handlowiec,
            handlowiec,
            handlowiec,
            admin,
            handlowiec,
            handlowiec,
            admin,
            handlowiec,
        ]
        for i, (name, industry, _label, phone, website) in enumerate(COMPANIES):
            company, created = Company.objects.get_or_create(
                name=name,
                defaults={
                    "industry": industry,
                    "phone": phone,
                    "website": f"https://www.{website}",
                    "owner": owners[i],
                    "city": random.choice(
                        ["Warszawa", "Krakow", "Wroclaw", "Poznan", "Gdansk", "Lodz"]
                    ),
                },
            )
            companies.append(company)
            if created:
                self.stdout.write(f"  Firma: {name}")
        self.stdout.write(f"  Lacznie firm: {len(companies)}")
        return companies

    # ------------------------------------------------------------------
    # Kontakty
    # ------------------------------------------------------------------

    def _create_contacts(self, companies):
        contacts = []
        for i, (first, last, position, email) in enumerate(CONTACTS):
            company = companies[i % len(companies)]
            contact, created = Contact.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "position": position,
                    "company": company,
                    "phone": f"50{i:01d}-{i:03d}-{i:03d}",
                },
            )
            contacts.append(contact)
        self.stdout.write(f"  Lacznie kontaktow: {len(contacts)}")
        return contacts

    # ------------------------------------------------------------------
    # Etapy workflow
    # ------------------------------------------------------------------

    def _ensure_workflow_stages(self):
        stages_data = [
            (1, "Nowy", "#6c757d"),
            (2, "Kwalifikacja", "#0d6efd"),
            (3, "Oferta", "#fd7e14"),
            (4, "Negocjacje", "#ffc107"),
            (5, "Zamkniety", "#198754"),
        ]
        stages = []
        for order, name, color in stages_data:
            stage, _ = WorkflowStage.objects.get_or_create(
                order=order, defaults={"name": name, "color": color}
            )
            stages.append(stage)
        self.stdout.write(f"  Etapy workflow: {len(stages)}")
        return stages

    # ------------------------------------------------------------------
    # Leady
    # ------------------------------------------------------------------

    def _create_leads(self, companies, contacts, handlowiec, stages):
        statuses = [
            Lead.Status.NOWY,
            Lead.Status.NOWY,
            Lead.Status.W_TOKU,
            Lead.Status.W_TOKU,
            Lead.Status.W_TOKU,
            Lead.Status.WYGRANA,
            Lead.Status.WYGRANA,
            Lead.Status.WYGRANA,
            Lead.Status.WYGRANA,
            Lead.Status.PRZEGRANA,
            Lead.Status.PRZEGRANA,
            Lead.Status.W_TOKU,
            Lead.Status.NOWY,
            Lead.Status.WYGRANA,
            Lead.Status.ANULOWANY,
        ]
        leads = []
        for i, title in enumerate(LEAD_TITLES):
            status = statuses[i]
            stage = stages[min(i % len(stages), len(stages) - 1)]
            closed_at = None
            if status in (
                Lead.Status.WYGRANA,
                Lead.Status.PRZEGRANA,
                Lead.Status.ANULOWANY,
            ):
                closed_at = timezone.now() - datetime.timedelta(
                    days=random.randint(1, 60)
                )
            lead, created = Lead.objects.get_or_create(
                title=title,
                defaults={
                    "company": companies[i % len(companies)],
                    "contact": contacts[i % len(contacts)],
                    "owner": handlowiec,
                    "stage": stage,
                    "status": status,
                    "value": random.choice(
                        [
                            "5000.00",
                            "12000.00",
                            "25000.00",
                            "50000.00",
                            "8000.00",
                            "15000.00",
                            "30000.00",
                            "100000.00",
                        ]
                    ),
                    "source": random.choice(
                        ["Polecenie", "Strona WWW", "Targi", "Cold call"]
                    ),
                    "closed_at": closed_at,
                },
            )
            leads.append(lead)
        self.stdout.write(f"  Lacznie leadow: {len(leads)}")
        return leads

    # ------------------------------------------------------------------
    # Umowy
    # ------------------------------------------------------------------

    def _create_deals(self, companies, leads, handlowiec):
        deal_statuses = [
            Deal.Status.AKTYWNA,
            Deal.Status.AKTYWNA,
            Deal.Status.AKTYWNA,
            Deal.Status.AKTYWNA,
            Deal.Status.ZREALIZOWANA,
            Deal.Status.ZREALIZOWANA,
            Deal.Status.ZREALIZOWANA,
            Deal.Status.ANULOWANA,
            Deal.Status.AKTYWNA,
            Deal.Status.ZREALIZOWANA,
        ]
        deals = []
        today = datetime.date.today()
        for i, title in enumerate(DEAL_TITLES):
            status = deal_statuses[i]
            close_date = today + datetime.timedelta(days=random.randint(-30, 120))
            signed_at = None
            if status == Deal.Status.ZREALIZOWANA:
                signed_at = today - datetime.timedelta(days=random.randint(1, 30))
            deal, created = Deal.objects.get_or_create(
                title=title,
                defaults={
                    "company": companies[i % len(companies)],
                    "owner": handlowiec,
                    "status": status,
                    "value": random.choice(
                        [
                            "10000.00",
                            "25000.00",
                            "50000.00",
                            "75000.00",
                            "120000.00",
                            "200000.00",
                            "15000.00",
                            "35000.00",
                        ]
                    ),
                    "close_date": close_date,
                    "signed_at": signed_at,
                },
            )
            deals.append(deal)
        self.stdout.write(f"  Lacznie umow: {len(deals)}")
        return deals

    # ------------------------------------------------------------------
    # Zadania
    # ------------------------------------------------------------------

    def _create_tasks(self, companies, leads, deals, admin, handlowiec):
        task_data = [
            (
                "Telekonferencja z Techsfera",
                Task.TaskType.TELEFON,
                Task.Priority.WYSOKI,
                Task.Status.DO_ZROBIENIA,
                1,
            ),
            (
                "Spotkanie z klientem BudMax",
                Task.TaskType.SPOTKANIE,
                Task.Priority.WYSOKI,
                Task.Status.W_TOKU,
                3,
            ),
            (
                "Wyslac oferte do HandelPro",
                Task.TaskType.EMAIL,
                Task.Priority.PILNY,
                Task.Status.DO_ZROBIENIA,
                0,
            ),
            (
                "Przygotowac umowe ramowa",
                Task.TaskType.ZADANIE,
                Task.Priority.SREDNI,
                Task.Status.DO_ZROBIENIA,
                7,
            ),
            (
                "Follow-up po targach",
                Task.TaskType.TELEFON,
                Task.Priority.NISKI,
                Task.Status.WYKONANE,
                -2,
            ),
            (
                "Prezentacja systemu ERP",
                Task.TaskType.SPOTKANIE,
                Task.Priority.WYSOKI,
                Task.Status.DO_ZROBIENIA,
                5,
            ),
            (
                "Weryfikacja dokumentacji",
                Task.TaskType.ZADANIE,
                Task.Priority.SREDNI,
                Task.Status.W_TOKU,
                2,
            ),
            (
                "Negocjacje kontraktu logistycznego",
                Task.TaskType.SPOTKANIE,
                Task.Priority.PILNY,
                Task.Status.DO_ZROBIENIA,
                1,
            ),
            (
                "Przygotowac raport kwartalny",
                Task.TaskType.ZADANIE,
                Task.Priority.NISKI,
                Task.Status.DO_ZROBIENIA,
                14,
            ),
            (
                "Odnowienie umowy serwisowej",
                Task.TaskType.ZADANIE,
                Task.Priority.SREDNI,
                Task.Status.DO_ZROBIENIA,
                30,
            ),
            (
                "Spotkanie z nowym klientem",
                Task.TaskType.SPOTKANIE,
                Task.Priority.WYSOKI,
                Task.Status.DO_ZROBIENIA,
                4,
            ),
            (
                "Wyslac przypomnienie o platnosci",
                Task.TaskType.EMAIL,
                Task.Priority.PILNY,
                Task.Status.WYKONANE,
                -1,
            ),
            (
                "Analiza potrzeb MediCare",
                Task.TaskType.INNE,
                Task.Priority.SREDNI,
                Task.Status.DO_ZROBIENIA,
                10,
            ),
            (
                "Konfiguracja platformy demo",
                Task.TaskType.ZADANIE,
                Task.Priority.WYSOKI,
                Task.Status.W_TOKU,
                3,
            ),
            (
                "Telekon z prawnikami",
                Task.TaskType.TELEFON,
                Task.Priority.WYSOKI,
                Task.Status.DO_ZROBIENIA,
                2,
            ),
            (
                "Weryfikacja NDA – OmniGroup",
                Task.TaskType.ZADANIE,
                Task.Priority.SREDNI,
                Task.Status.DO_ZROBIENIA,
                6,
            ),
            (
                "Aktualizacja CRM po spotkaniu",
                Task.TaskType.ZADANIE,
                Task.Priority.NISKI,
                Task.Status.WYKONANE,
                -3,
            ),
            (
                "Onboarding nowego klienta",
                Task.TaskType.INNE,
                Task.Priority.WYSOKI,
                Task.Status.DO_ZROBIENIA,
                7,
            ),
            (
                "Cold call – lista prospektow",
                Task.TaskType.TELEFON,
                Task.Priority.SREDNI,
                Task.Status.DO_ZROBIENIA,
                1,
            ),
            (
                "Zamkniecie kwartalu – raporty",
                Task.TaskType.ZADANIE,
                Task.Priority.PILNY,
                Task.Status.DO_ZROBIENIA,
                0,
            ),
        ]
        today = datetime.date.today()
        count = 0
        for i, (title, task_type, priority, status, days_offset) in enumerate(
            task_data
        ):
            due_dt = timezone.make_aware(
                datetime.datetime.combine(
                    today + datetime.timedelta(days=days_offset),
                    datetime.time(9 + i % 8, 0),
                )
            )
            assigned = handlowiec if i % 3 != 0 else admin
            completed_at = None
            if status == Task.Status.WYKONANE:
                completed_at = timezone.now() - datetime.timedelta(
                    days=random.randint(1, 10)
                )
            Task.objects.get_or_create(
                title=title,
                defaults={
                    "task_type": task_type,
                    "priority": priority,
                    "status": status,
                    "due_date": due_dt,
                    "assigned_to": assigned,
                    "created_by": admin,
                    "company": companies[i % len(companies)],
                    "lead": leads[i % len(leads)] if i < len(leads) else None,
                    "completed_at": completed_at,
                },
            )
            count += 1
        self.stdout.write(f"  Lacznie zadan: {count}")

    # ------------------------------------------------------------------
    # Notatki
    # ------------------------------------------------------------------

    def _create_notes(self, companies, leads, deals, contacts, handlowiec):
        for i, content in enumerate(NOTE_CONTENTS):
            Note.objects.get_or_create(
                content=content,
                defaults={
                    "author": handlowiec,
                    "company": companies[i % len(companies)],
                    "lead": leads[i % len(leads)] if i < 5 else None,
                    "deal": deals[i % len(deals)] if 5 <= i < 8 else None,
                    "contact": contacts[i % len(contacts)],
                },
            )
        self.stdout.write(f"  Lacznie notatek: {len(NOTE_CONTENTS)}")

    # ------------------------------------------------------------------
    # Logi aktywnosci
    # ------------------------------------------------------------------

    def _create_activity_logs(self, admin, handlowiec, companies, leads, deals):
        entries = []
        for company in companies[:5]:
            entries.append(
                (handlowiec, ActivityLog.Action.UTWORZONO, company, "Firma dodana")
            )
            entries.append((handlowiec, ActivityLog.Action.WYSWIETLONO, company, ""))
        for lead in leads[:8]:
            entries.append(
                (handlowiec, ActivityLog.Action.UTWORZONO, lead, "Lead dodany")
            )
            entries.append(
                (handlowiec, ActivityLog.Action.ZAKTUALIZOWANO, lead, "Zmiana statusu")
            )
        for deal in deals[:5]:
            entries.append((admin, ActivityLog.Action.UTWORZONO, deal, "Umowa dodana"))
        for entry in entries:
            user, action, obj, desc = entry
            ActivityLog.objects.create(
                user=user,
                action=action,
                model_name=obj.__class__.__name__,
                object_id=obj.pk,
                object_repr=str(obj)[:200],
                description=desc,
            )
        self.stdout.write(f"  Lacznie logow: {len(entries)}")
