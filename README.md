# Spendly — Full-Stack Expense Tracker

**Live Demo:** https://spendly-expense-tracker-production.up.railway.app

Spendly is a production-deployed Flask application where users can register, log in, manage expenses (create, edit, delete), filter by date ranges, and view analytics with multiple visualizations.

## Why this project stands out

- End-to-end feature ownership: auth, CRUD, filtering, analytics, deployment
- Security-first patterns: hashed passwords, CSRF checks, ownership authorization
- Real product flow: dashboard, profile, analytics, and clean UX across pages
- Deployed and publicly accessible for quick recruiter review

## Features

- User authentication (register/login/logout)
- Expense CRUD (add, edit, delete)
- Date filtering (all-time, presets, custom range)
- Analytics dashboard with:
  - Monthly spending trend
  - Category distribution
  - Weekday spending pattern
  - Top-expense table
- Responsive UI with Jinja2 templates + vanilla CSS/JS

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** Jinja2 templates, vanilla CSS, vanilla JavaScript
- **Testing:** pytest, pytest-flask
- **Deployment:** Railway

## Demo Credentials

- **Email:** `demo@spendly.com`
- **Password:** `demo123`

## Local Setup

```bash
git clone https://github.com/VikasDataSync/Expense_Tracker.git
cd Expense_Tracker
python -m pip install -r requirements.txt
python app.py
```

App runs on `http://127.0.0.1:5001` locally.

## Project Structure

```text
Expense_Tracker/
├── app.py
├── database/
│   ├── db.py
│   └── queries.py
├── templates/
├── static/
│   ├── css/
│   └── js/
├── tests/
└── requirements.txt
```

## Quality Signals

- Automated tests with `pytest`
- Parameterized SQL queries (no ORM)
- Clear separation of concerns (routes, DB helpers, templates, JS)
- Public deployment and reproducible local setup

## Author

**Vikas Singh**  
GitHub: https://github.com/VikasDataSync
