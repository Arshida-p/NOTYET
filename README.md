# NOTYET ⚡

> **Discover what your neighbourhood is missing. Empower local businesses to fill the gap.**

NOTYET is a community-driven demand intelligence web application that bridges the gap between everyday resident needs and local entrepreneurial opportunities. Residents highlight and validate the shops, clinics, services, and amenities missing in their neighborhood, giving local entrepreneurs and small businesses verified customer demand before launching.

---

## 📁 Project Folder Structure

```text
NOTYET/
├── app.py                     # Main Flask application & route controllers
├── database.py                # Safe SQLite connection pool & idempotent schema initialization
├── schema.sql                 # Database table definitions (CREATE TABLE IF NOT EXISTS)
├── requirements.txt           # Python dependencies (Flask)
├── .env.example               # Safe environment variable configuration template
├── .gitignore                 # Excludes local databases, caches, venvs, and secrets
├── README.md                  # Comprehensive setup & project documentation
│
├── static/
│   ├── css/
│   │   └── style.css          # Shared modern design system (dark mode, glassmorphism, cards)
│   └── js/
│       └── main.js            # Responsive mobile navbar & alert dismissal micro-interactions
│
└── templates/
    ├── base.html              # Shared layout (responsive navigation, alerts, footer)
    ├── index.html             # Feature 1: Homepage (hero, dynamic metrics, recent needs)
    ├── needs.html             # Feature: Browse Community Needs (filters, search, status tags)
    ├── report.html            # Feature 2: Report an unmet community need form
    ├── validation.html        # Feature 3: Community voting & demand validation hub
    └── opportunities.html     # Feature 4: Local business market demand intelligence
```

---

## ✨ Core Features

1. **Homepage (`/`)**: Welcoming discovery hub with real-time aggregate metrics dynamically queried from SQLite (total needs recorded, active neighbourhoods, community validations), 3-step workflow, and recent community reports.
2. **Browse Community Needs (`/needs`, `/browse`)**: Full directory of community requests with responsive cards showing title, description, category icon, neighbourhood area, validation count, and color-coded status badges (`Open Need`, `In Discussion`, `Need Met`). Includes multi-parameter filtering:
   - **Keyword Search**: Filter by title or description query (`?q=...`)
   - **Category Filter**: Filter by service domain (`?category=...`)
   - **Neighbourhood Filter**: Filter by district or town (`?neighborhood=...`)
   - **Status Filter**: Filter by `open`, `in_discussion`, or `met` (`?status=...`)
   - **Graceful Empty State**: Helpful reset controls and empty state prompts when zero records match.
3. **Report a Need (`/report`)**: Frictionless form allowing residents to submit missing services, stores, or amenities with input validation (title, category, neighbourhood, zip code, reporter alias, description).
4. **Community Validation (`/validation`)**: Upvoting feed (`POST /validate/<id>`) allowing neighbours to add "+1 I Need This Too", increasing local civic demand visibility.
5. **Business Opportunities (`/opportunities`)**: Aggregated commercial demand signals, market demand by category breakdown, and direct business lead registration for local entrepreneurs.

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- **Python 3.10+** installed on your system. Verify with:
  ```bash
  python --version
  ```

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/<your-username>/NOTYET.git
cd NOTYET
```

---

### Step 2: Create & Activate a Virtual Environment

Creating an isolated virtual environment is recommended:

- **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once)*

- **Windows (Command Prompt):**
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```

- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4: Configure Environment (Optional)

Copy the example environment file to configure local settings:

- **Windows:**
  ```cmd
  copy .env.example .env
  ```
- **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

---

### Step 5: Run the Application

```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🛡️ Safe Database Design (Zero Data Loss)

- **Automatic SQLite Initialization**: The local database file `notyet.db` is automatically created on first launch if it does not exist.
- **Idempotent by Design**: All table definitions in `schema.sql` utilize `CREATE TABLE IF NOT EXISTS`. Restarting or re-running the application **never deletes, drops, or overwrites existing records**.
- **Starter Data**: Initial seed needs are only inserted if the `needs` table is completely empty (count = 0).
- **Git Excluded**: `notyet.db` is strictly excluded in `.gitignore` to prevent database merge conflicts and keep local test records private.
- **Manual Safe Initialization CLI**:
  ```bash
  flask --app app init-db
  ```

---

## 🎨 Design System & Aesthetics

- **Color Tokens**: Dark slate backgrounds (`--bg-dark: #090d16`, `--bg-card: #182238`), vibrant mint-teal accents (`--accent-teal: #10b981`), violet accents (`--accent-indigo: #6366f1`), and amber validation pills (`--accent-amber: #f59e0b`).
- **Typography**: Google Fonts `Plus Jakarta Sans` for titles and `Inter` for interface elements and reading copy.
- **Components**: Reusable card grid (`.cards-grid`), need cards (`.need-card`), status badges (`.status-badge`), filter bars (`.filter-bar`), and empty states (`.empty-box`).
- **Responsive**: Fully responsive flexbox and CSS Grid layout with mobile navigation toggle (`main.js`).

---

## 🔒 Security Best Practices

- **Parameterized Queries**: All database lookups (including search queries and multi-filter criteria) use parameterized SQL placeholders (`?`) to prevent SQL injection.
- **Secrets Isolation**: Application secret keys are read from environment variables (`SECRET_KEY`) with a fallback for local development. Real secrets are never hardcoded or committed to version control.
- **Input Sanitization**: Length validation and category taxonomy checks protect form submissions.
