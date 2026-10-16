# CampusSpace â€” Smart Campus Room Finder
> **â€œThe Campus Has Space. Students Donâ€™t.â€**  
> *Hackathon Round 1 MVP | Full-Stack Platform with Integrated Authentication & Dark Mode*

---

## ðŸ“Œ Executive Summary
**CampusSpace** addresses a systemic issue in modern universities: student study groups, clubs, and hackathon teams struggle to secure rooms, even as classrooms and labs sit idle due to fragmented, siloed campus scheduling.

CampusSpace bridges this divide by turning scheduling and event datasets into **transparent, explainable, conflict-free room recommendations** with enterprise-grade PBKDF2 authentication, role-based controls, and space utilization analytics.

---

## ðŸš€ Key Features (Round 1 MVP)

### 1. ðŸ” Enterprise Authentication & Role-Based Access
- **PBKDF2-HMAC-SHA256 Hashing:** 100,000 iterations with per-user cryptographic salts. Passwords are never stored in plaintext.
- **Dual Login Support:** Authenticate using university username or campus email (case-insensitive).
- **Interactive Password Visibility:** Show/hide password control toggle.
- **Public Room Discovery / Guest Mode:** Visitors can explore room inventories and search schedules without mandatory login.
- **Role-Based Protection:** Server-side privilege enforcement for `Student`, `Faculty`, `Administrator`, and `Club Organizer` personas.
- **Admin Control Center:** Exclusive space allocation policy recommendations and CSV utilization audit downloads for Administrators.

### 2. ðŸ” Explainable 2-Stage Room Finder
- **Stage 1 (Hard Constraints):** Strictly filters out rooms by capacity, required facilities (projector, workstations, ADA wheelchair accessibility), and confirmed scheduling conflicts.
- **Stage 2 (Multicriteria Ranking):** Scores feasible rooms on capacity fit efficiency (minimizing wasted seats), amenities, and building preference.
- **Dynamic Explanations:** Generates evidence-based rationales for why each room was chosen (e.g. attendee fit, equipment match, 0 schedule overlaps).
- **Intelligent Constraint Relaxation:** When 0 rooms match, provides automatic relaxation suggestions (e.g. shifting time slot or relaxing workstation constraints).

### 3. ðŸŒ™ Responsive Dark / Light Mode
- Live toggle between **Crisp Light SaaS Palette** (Navy, Teal, Slate) and **Modern Dark Mode** (Deep Navy/Slate `#0F172A`, Dark Cards `#1E293B`, Teal accents `#14B8A6`).
- Theme auto-synchronized across Streamlit forms, BaseWeb dropdowns, and Plotly charts (`plotly_white` / `plotly_dark`).

### 4. ðŸ›ï¸ Interactive Room Explorer & Timetable Inspector
- Search and filter all 120 rooms by building, room type, floor, and equipment.
- Inspect any room's full timetable: weekly recurring classes and dated special events.

### 5. ðŸ“Š Space Utilization & Demand Analytics
- Calculates verified weekly occupancy proxies against campus operating windows (60 hrs/week).
- Compares hourly student demand against academic class loads to highlight allocation gaps.
- Identifies underutilized rooms prime for student access during idle hours.

### 6. â„¹ï¸ Data Health & Formal Data Dictionary
- Automated audit report on dataset health, schema validation, and missing values.
- Complete data dictionary for all four benchmark datasets.

---

## ðŸ§ª Demo Evaluator Accounts

For hackathon jury evaluation, the following pre-configured accounts are active (or use the **One-Click Quick Login** buttons on the login screen):

| Role | Username | Email | Demo Password | Persona Name | Key Privileges |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Student** | `student` | `student@campus.edu` | `campus123` | Alex Kumar | Room search, conflict checking, public analytics |
| **Faculty** | `faculty` | `faculty@campus.edu` | `faculty456` | Dr. Priya Sharma | Priority room search, department analytics |
| **Administrator** | `admin` | `admin@campus.edu` | `admin789` | Campus Admin | Full access, space reallocation policy, audit CSV export |
| **Club Organizer** | `club` | `club@campus.edu` | `club321` | Rohan Verma | Event room matching, multi-slot feasibility |
| **Visitor / Guest** | *N/A* | *N/A* | *None (1-click)* | Campus Visitor | Public room discovery & schedule lookup |

---

## ðŸ“‚ Project Architecture

```
EternX/
â”œâ”€â”€ app.py                      # Main Streamlit application (Login + 5 Dashboards)
â”œâ”€â”€ requirements.txt            # Python dependencies
â”œâ”€â”€ README.md                   # System documentation & setup guide
â”œâ”€â”€ .streamlit/
â”‚   â””â”€â”€ config.toml             # Theme configuration (high-contrast text colors)
â”œâ”€â”€ assets/
â”‚   â”œâ”€â”€ logo.svg                # Vector branding logo
â”‚   â””â”€â”€ custom.css              # Custom SaaS styling rules
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ rooms.csv               # 120 campus room profiles
â”‚   â”œâ”€â”€ class_schedule.csv      # 5,000 weekly class schedule records
â”‚   â”œâ”€â”€ events.csv              # 1,800 scheduled events
â”‚   â”œâ”€â”€ room_requests.csv       # 5,000 unallocated student demand requests
â”‚   â””â”€â”€ README.txt              # Dataset provenance and join keys
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ auth.py                 # PBKDF2 hashing, verify, user store & roles
â”‚   â”œâ”€â”€ data_loader.py          # Data ingestion and type casting
â”‚   â”œâ”€â”€ data_validation.py      # Schema verification & data dictionary
â”‚   â”œâ”€â”€ availability.py         # Interval overlap and conflict detection
â”‚   â”œâ”€â”€ recommendation.py       # 2-stage ranking engine with dynamic explanations
â”‚   â””â”€â”€ analytics.py            # Utilization metrics & demand insights
â””â”€â”€ tests/
    â”œâ”€â”€ __init__.py
    â”œâ”€â”€ test_auth.py            # Unit tests for authentication & security
    â”œâ”€â”€ test_availability.py    # Unit tests for conflict detection
    â””â”€â”€ test_recommendations.py # Unit tests for filtering and ranking
```

---

## âš™ï¸ Installation & Quickstart

### Prerequisites
- Python 3.9+ (Python 3.10 - 3.14 supported)
- pip package manager

### 1. Install Dependencies
```bash
py -m pip install -r requirements.txt
```

### 2. Run the Application
```bash
py -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Automated Unit Tests (15 Tests)
```bash
py -m pytest tests/ -v
```
All 15 Tests verify:
- PBKDF2 password hashing & verification
- Username & email authentication
- Empty & invalid credentials rejection
- Session state management & role checks
- Interval overlap & weekday parsing
- Room class & event conflict detection
- Capacity & facility filtering
- Empty state & constraint relaxation

---

## ðŸ“ Data Provenance & Methodology

### Dataset Overview
1. **`rooms.csv` (120 rows):** Real room profiles across 5 buildings (`Central`, `East`, `North`, `South`, `West`). Capacities range from 15 to 179 seats.
2. **`class_schedule.csv` (5,000 rows):** Weekly recurring department classes (`Mon` to `Sat`, 08:00 to 18:00).
3. **`events.csv` (1,800 rows):** Specific dated events (`2025-08-01` to `2025-11-28`) with actual vs expected attendance.
4. **`room_requests.csv` (5,000 rows):** Student & club room requests representing pre-allocation demand.

### Scheduling Assumptions
- **Open-interval overlap:** Conflicting slots satisfy `start1 < end2 AND end1 > start2`.
- **Recurring vs Dated:** Class schedules repeat weekly by weekday; special events apply exclusively to their specific date.
- **Unconfirmed Requests:** Room requests are treated as unallocated demand rather than confirmed bookings.

---

## ðŸ”® Roadmap: Round 1 vs Round 2

| Feature | Round 1 (Completed) | Round 2 (Planned) |
| :--- | :---: | :---: |
| **Explainable Recommendation Engine** | âœ… Yes | Enhanced Multi-Objective |
| **Real Conflict Checking (Classes & Events)** | âœ… Yes | Real-time Webhook Sync |
| **PBKDF2 Role-Based Authentication** | âœ… Yes | University SSO / SAML / OAuth2 |
| **Constraint Relaxation Alternatives** | âœ… Yes | Automated Multi-Slot Bundling |
| **Dark & Light Mode Support** | âœ… Yes | Custom University Accent Themes |
| **Space Utilization Analytics** | âœ… Yes | ML Demand Forecasting |
| **Administrator Policy & Audit Export** | âœ… Yes | Automated ERP Reservation Push |
| **Ghost-Booking Detection** | Roadmap | ML Attendance Discrepancy Model |

