# Spec: Edit Expenses

## Overview
This step adds the ability for logged-in users to edit their existing expenses. Students will implement a form to update the amount, category, date, and description of any expense they previously recorded. This completes the "U" (Update) in the CRUD flow and teaches permission checking (users can only edit their own expenses) and form handling with existing data.

## Depends on
- Step 02 (Registration) — User accounts exist
- Step 03 (Login/Auth) — Session-based authentication
- Step 07 (Add Expenses) — Expenses exist and form validation is in place

## Routes
- `GET /expenses/<id>/edit` — Display edit form with pre-filled expense data (logged-in users only)
- `POST /expenses/<id>/edit` — Process the edit form submission and update expense (logged-in users only)

## Database changes
Add a new function to `database/db.py`:
- `get_expense_by_id(expense_id)` — Retrieve a single expense by ID
- `update_expense(expense_id, user_id, amount, category, date, description)` — Update an expense if it belongs to the user; return success/failure

No new tables or columns needed.

## Templates
- **Create:** `templates/edit_expense.html` — Form nearly identical to `add_expense.html` but with pre-filled values and an "Update Expense" button
- **Modify:** None

## Files to change
- `app.py` — Implement `/expenses/<int:id>/edit` route (GET and POST)
- `database/db.py` — Add `get_expense_by_id()` and `update_expense()` functions

## Files to create
- `templates/edit_expense.html` — Edit form template (based on `add_expense.html`)

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use parameterized queries only
- Parameterised queries only — prevent SQL injection
- Passwords hashed with werkzeug — not applicable here, but reference the pattern
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Users can only edit expenses they created — check `user_id` matches
- Reuse `validate_expense_form()` to validate input
- Use CSRF tokens for form security (follow the pattern in `add_expense()`)
- If expense not found or belongs to another user, return 404 or redirect
- After successful update, redirect to dashboard with success flash message

## Definition of done
- [ ] `get_expense_by_id()` retrieves an expense by ID
- [ ] `update_expense()` updates an expense and validates ownership
- [ ] `GET /expenses/<id>/edit` displays form with pre-filled data
- [ ] `POST /expenses/<id>/edit` updates the expense after validation
- [ ] User cannot edit another user's expense (403 or redirect)
- [ ] User cannot edit a non-existent expense (404)
- [ ] Form validation works (same rules as add expense)
- [ ] Flash message shows on success
- [ ] Redirect to dashboard after update
- [ ] Edit form looks consistent with add expense form
- [ ] CSRF protection is in place
