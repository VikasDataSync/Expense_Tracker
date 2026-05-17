# Spendly — Expense Tracking Web Application

Spendly is a full-stack Flask application for personal expense management, built with server-rendered templates and deployed publicly.

**Live Application:** https://spendly-expense-tracker-production.up.railway.app

## Key Capabilities

- User authentication: registration, login, and logout
- Expense lifecycle management: create, edit, and delete
- Date-based filtering: presets and custom ranges
- Analytics dashboard:
  - Monthly spend trend
  - Category distribution
  - Weekday spend pattern
  - Top-expense breakdown

## Technical Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **Frontend:** Jinja2, vanilla CSS, vanilla JavaScript
- **Testing:** pytest, pytest-flask
- **Hosting:** Railway

## Architecture Overview

```text
Expense_Tracker/
├── app.py                 # Route layer and request handling
├── database/
│   ├── db.py              # Connection + write helpers
│   └── queries.py         # Read/query helpers
├── templates/             # Jinja2 templates
├── static/
│   ├── css/               # Styling
│   └── js/                # Frontend behavior and chart rendering
├── tests/                 # Route and query test coverage
└── requirements.txt
```

## Security and Quality Practices

- Password hashing with Werkzeug
- CSRF token validation on mutating forms
- Ownership authorization for expense updates/deletes
- Parameterized SQL queries throughout (no ORM)
- Automated regression coverage with `pytest`

## Demo Access

- **Email:** `demo@spendly.com`
- **Password:** `demo123`

## Run Locally

```bash
git clone https://github.com/VikasDataSync/Expense_Tracker.git
cd Expense_Tracker
python -m pip install -r requirements.txt
python app.py
```

Local URL: `http://127.0.0.1:5001`

## Author

**Vikas Singh**  
GitHub: https://github.com/VikasDataSync
