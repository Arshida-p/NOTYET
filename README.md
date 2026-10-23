# NOTYET ⚡

> **Discover what your neighbourhood is missing. Empower local businesses to fill the gap.**

NOTYET is a hackathon web application that bridges the gap between everyday community needs and local entrepreneurial opportunities. Residents highlight and validate the shops, clinics, services, and amenities missing in their neighborhood, giving local entrepreneurs and small businesses verified customer demand before launching.

---

## 📁 Project Folder Structure

```text
NotYet/
├── app.py                     # Main Flask application & planned route handlers
├── database.py                # Safe SQLite connection pool & idempotent schema init
├── schema.sql                 # Database table definitions (CREATE TABLE IF NOT EXISTS)
├── requirements.txt           # Python dependencies (Flask)
├── README.md                  # Beginner-friendly documentation & Windows setup guide
│
├── static/
│   ├── css/
│   │   └── style.css          # Shared modern design system (variables, cards, forms, nav)
│   └── js/
│       └── main.js            # Responsive mobile navbar & notification dismissals
│
└── templates/
    ├── base.html              # Shared HTML layout (responsive nav, alerts, container, footer)
    ├── index.html             # Feature 1: Homepage (hero, live stats, pillars, recent needs)
    ├── report.html            # Feature 2 (Scaffold): Report a missing community need
    ├── validation.html        # Feature 3 (Scaffold): Community voting & validation feed
    └── opportunities.html     # Feature 4 (Scaffold): Local business market demand intelligence
```

---

## 🚀 How to Run on Windows (Beginner-Friendly)

### Prerequisites
Make sure you have **Python 3.10+** installed on your Windows machine. You can verify this by opening **PowerShell** or **Command Prompt** and typing:
```powershell
python --version
```

### Option A: Quickstart (Direct Run)

1. Open **Command Prompt** or **PowerShell** in the `NotYet` folder:
   ```powershell
   cd c:\Users\dell\OneDrive\Desktop\NotYet
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Start the application:
   ```powershell
   python app.py
   ```

4. Open your browser and visit:
   ```text
   http://127.0.0.1:5000
   ```

---

### Option B: Using a Virtual Environment (Recommended Practice)

Creating a virtual environment ensures your project dependencies don't interfere with other Python tools on your PC:

1. Create a virtual environment named `venv`:
   ```powershell
   python -m venv venv
   ```

2. Activate the virtual environment:
   * **In PowerShell:**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     *(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once)*
   * **In Command Prompt (cmd.exe):**
     ```cmd
     venv\Scripts\activate.bat
     ```

3. Install requirements inside the environment:
   ```powershell
   pip install -r requirements.txt
   ```

4. Run the app:
   ```powershell
   python app.py
   ```

---

## 🛡️ Safe Database Design (Zero Data Loss)

- The database file `notyet.db` is automatically created on first run.
- **Idempotent by design**: All tables use `CREATE TABLE IF NOT EXISTS`. Restarting or re-running `database.py` **never deletes or drops existing records**.
- You can manually re-run safe database initialization anytime via:
  ```powershell
  flask --app app init-db
  ```
- **No fake statistics**: Aggregate numbers (Needs count, Active neighborhoods, Neighbor validations) are dynamically computed via direct SQL queries against real user records.

---

## 🗺️ Feature Roadmap & Team Collaboration

The shared foundation provides pre-built routes, database models, and starter templates for all 4 features:

| Feature | Route | Lead Focus / Expansion Points |
| :--- | :--- | :--- |
| **1. Homepage** | `/` | Welcoming hero, dynamic stats bar, and live community need cards. |
| **2. Report a Need** | `/report` | Form submission (`POST /report`), category selection, description, and area input. Ready for photo uploads or geolocation tags. |
| **3. Community Validation** | `/validation` | Upvoting (`POST /validate/<id>`), category/area filtering, and neighbor verification. Ready for comments and discussion threads. |
| **4. Business Opportunities** | `/opportunities` | Translates validated demand into market signals for local business owners. Ready for revenue estimates, PDF reports, and direct business lead registration. |

---

## 🎨 Shared Styling Conventions (`static/css/style.css`)

All components share a consistent modern design system:
- **Color Tokens**: Dark slate backgrounds (`--bg-dark`, `--bg-card`), vibrant mint-teal accents (`--accent-teal`), violet highlights (`--accent-indigo`), and amber validation pills (`--accent-amber`).
- **Typography**: Google Fonts `Plus Jakarta Sans` for headers and `Inter` for body copy.
- **Components**: `.btn`, `.need-card`, `.form-card`, `.metric-card`, `.badge-tag`, `.filter-bar`.
- **Responsive**: Flexbox and CSS Grid layouts that automatically adjust between mobile and desktop screens.
