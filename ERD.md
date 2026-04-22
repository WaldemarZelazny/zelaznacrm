# ZelaznaCRM — Diagram ERD (Entity-Relationship Diagram)

Diagram relacji między modelami systemu ZelaznaCRM.
Wygenerowany: Kwiecień 2026 | Django 5.x | 10 modeli, 9 aplikacji

---

## Diagram Mermaid

```mermaid
erDiagram

    User {
        int id PK
        string username
        string first_name
        string last_name
        string email
        string password
        bool is_active
        bool is_staff
    }

    UserProfile {
        int id PK
        int user_id FK
        string role
        string phone
        ImageField avatar
        datetime created_at
    }

    Company {
        int id PK
        int owner_id FK
        string name
        string nip
        string address
        string city
        string postal_code
        string phone
        string email
        string website
        string industry
        text notes
        bool is_active
        datetime created_at
        datetime updated_at
    }

    Contact {
        int id PK
        int company_id FK
        int owner_id FK
        string first_name
        string last_name
        string email
        string phone
        string position
        string department
        text notes
        bool is_active
        datetime created_at
        datetime updated_at
    }

    WorkflowStage {
        int id PK
        string name
        int order
        string color
        bool is_active
    }

    Lead {
        int id PK
        int company_id FK
        int contact_id FK
        int owner_id FK
        int stage_id FK
        string title
        string status
        string source
        decimal value
        text description
        datetime created_at
        datetime updated_at
        datetime closed_at
    }

    Deal {
        int id PK
        int company_id FK
        int lead_id FK
        int owner_id FK
        string title
        string status
        decimal value
        date signed_at
        date close_date
        text description
        datetime created_at
        datetime updated_at
    }

    Task {
        int id PK
        int company_id FK
        int lead_id FK
        int deal_id FK
        int assigned_to_id FK
        int created_by_id FK
        string title
        string task_type
        string priority
        string status
        datetime due_date
        datetime completed_at
        text description
        datetime created_at
        datetime updated_at
    }

    Document {
        int id PK
        int company_id FK
        int lead_id FK
        int deal_id FK
        int created_by_id FK
        string title
        string doc_type
        FileField file
        text description
        datetime created_at
        datetime updated_at
    }

    Note {
        int id PK
        int author_id FK
        int company_id FK
        int lead_id FK
        int deal_id FK
        int contact_id FK
        text content
        datetime created_at
        datetime updated_at
    }

    ActivityLog {
        int id PK
        int user_id FK
        string action
        string model_name
        int object_id
        string object_repr
        text description
        string ip_address
        datetime created_at
    }

    %% === RELACJE ===

    User ||--|| UserProfile : "profil (OneToOne)"
    User ||--o{ Company : "opiekun (owner)"
    User ||--o{ Contact : "opiekun (owner)"
    User ||--o{ Lead : "handlowiec (owner)"
    User ||--o{ Deal : "handlowiec (owner)"
    User ||--o{ Task : "przypisane do (assigned_to)"
    User ||--o{ Task : "utworzone przez (created_by)"
    User ||--o{ Document : "wgrał (created_by)"
    User ||--o{ Note : "autor"
    User ||--o{ ActivityLog : "wykonał akcję"

    Company ||--o{ Contact : "kontakty"
    Company ||--o{ Lead : "leady (CASCADE)"
    Company ||--o{ Deal : "umowy (CASCADE)"
    Company ||--o{ Task : "zadania (SET_NULL)"
    Company ||--o{ Document : "dokumenty (SET_NULL)"
    Company ||--o{ Note : "notatki (SET_NULL)"

    WorkflowStage ||--o{ Lead : "etap Kanban (PROTECT)"

    Lead }o--|| Company : "firma"
    Lead }o--o| Contact : "kontakt (opcjonalny)"
    Lead }o--o| User : "właściciel"
    Lead }o--|| WorkflowStage : "etap"
    Lead ||--o{ Deal : "umowy z leada (SET_NULL)"
    Lead ||--o{ Task : "zadania (SET_NULL)"
    Lead ||--o{ Document : "dokumenty (SET_NULL)"
    Lead ||--o{ Note : "notatki (SET_NULL)"

    Deal }o--|| Company : "firma (CASCADE)"
    Deal }o--o| Lead : "lead źródłowy (SET_NULL)"
    Deal }o--o| User : "właściciel"
    Deal ||--o{ Task : "zadania (SET_NULL)"
    Deal ||--o{ Document : "dokumenty (SET_NULL)"
    Deal ||--o{ Note : "notatki (SET_NULL)"

    Contact }o--|| Company : "firma (CASCADE)"
    Contact }o--o| User : "opiekun"
    Contact ||--o{ Lead : "leady (SET_NULL)"
    Contact ||--o{ Note : "notatki (SET_NULL)"
```

---

## Legenda relacji

| Symbol Mermaid | Znaczenie | Django on_delete |
|----------------|-----------|-----------------|
| `\|\|--\|\|` | Jeden do jeden | OneToOneField |
| `\|\|--o{` | Jeden do wielu (wymagany) | CASCADE / PROTECT |
| `}o--o\|` | Wiele do jeden (opcjonalny FK) | SET_NULL |
| `}o--\|\|` | Wiele do jeden (wymagany FK) | CASCADE |

---

## Podsumowanie modeli

| Model | Aplikacja | Klucze obce (FK) | Opis |
|-------|-----------|-----------------|------|
| `User` | django.auth | — | Wbudowany model Django |
| `UserProfile` | accounts | User (OneToOne) | Rozszerzenie profilu (rola, telefon, avatar) |
| `Company` | companies | User (owner) | Firma-klient CRM |
| `Contact` | contacts | Company, User (owner) | Osoba kontaktowa w firmie |
| `WorkflowStage` | leads | — | Etap lejka Kanban |
| `Lead` | leads | Company, Contact, User, WorkflowStage | Szansa sprzedaży |
| `Deal` | deals | Company, Lead, User | Umowa handlowa |
| `Task` | tasks | Company, Lead, Deal, User×2 | Zadanie CRM z terminem |
| `Document` | documents | Company, Lead, Deal, User | Plik lub dokument PDF |
| `Note` | notes | User, Company, Lead, Deal, Contact | Notatka tekstowa |
| `ActivityLog` | reports | User | Niemutowalny log zdarzeń |

---

## Renderowanie diagramu

Aby wyświetlić diagram Mermaid:
- **VS Code:** rozszerzenie *Markdown Preview Mermaid Support*
- **GitHub:** diagramy Mermaid renderowane natywnie w plikach `.md`
- **Online:** [mermaid.live](https://mermaid.live)
- **PNG:** plik `ERD.png` w katalogu głównym projektu
