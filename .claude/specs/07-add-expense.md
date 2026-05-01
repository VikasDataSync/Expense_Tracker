# Spec: Add Expense

## Overview
This step implements the first real expense-write flow in Spendly by replacing the `/expenses/add` placeholder with a protected form page and POST handler. Logged-in users can submit amount, category, date, and description to create a new expense record tied to their account, then return to the dashboard/profile flow with updated numbers. This is the first CRUD action in the roadmap and enables the remaining edit/delete steps to build on a real create path.

## Depends on
- Step 01 — Database setup (`expenses` table and `get_db()` are available)
- Step 03 — Login and logout (`session["user_id"]` auth guard exists)
- Step 05 — Profile/backend query wiring (newly added rows appear in profile data)
- Step 06 — Date-filtered profile data (new rows participate in filtered views)

## Routes
- `GET /expenses/add` — render add-expense form — logged-in
- `POST /expenses/add` — validate form, insert expense, redirect with flash message — logged-in

## Database changes
No database changes.

## Templates
- **Create:** `templates/add_expense.html` — form page for adding an expense (amount, category, date, description) with validation-error display
- **Modify:** `templates/dashboard.html` — keep/update "Add expense" CTA target so it points to `url_for("add_expense")` consistently
- **Modify:** `templates/profile.html` — optionally add a prominent "Add expense" CTA that links to the new form route

## Files to change
- `app.py`
- `database/db.py`
- `templates/dashboard.html`
- `templates/profile.html`
- `static/css/style.css`

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route must be session-protected using existing `session.get("user_id")` pattern
- Validate required fields server-side: `amount`, `category`, `date`
- `amount` must be parsed as numeric and greater than 0
- `category` must be restricted to the existing app category set (Food, Transport, Bills, Health, Entertainment, Shopping, Other)
- `date` must be valid ISO format (`YYYY-MM-DD`) and not malformed
- On validation failure, re-render form with entered values preserved and clear error message
- On success, insert using a parameterised `INSERT INTO expenses (...) VALUES (?, ?, ?, ?, ?)` tied to `session["user_id"]`
- Keep SQL operations in `database/db.py` helper(s), not inline in route logic
- Use `url_for()` for redirects and links; do not hardcode paths in templates

## Definition of done
- [ ] Logged-out user visiting `/expenses/add` is redirected to `/login`
- [ ] Logged-in user visiting `/expenses/add` sees the add-expense form page
- [ ] Submitting valid form data creates exactly one new row in `expenses` for the logged-in user
- [ ] Successful submit redirects to a post-submit page (dashboard or profile) with a success flash
- [ ] Submitting missing required fields shows validation errors and does not insert a row
- [ ] Submitting non-numeric or non-positive amount shows validation error and does not insert a row
- [ ] Submitting an invalid date format shows validation error and does not insert a row
- [ ] Submitting an out-of-list category is rejected and does not insert a row
- [ ] Newly added expense appears in recent transactions and updates summary totals after redirect
- [ ] `pytest` passes with add-expense route/helper tests included for success and validation failures
