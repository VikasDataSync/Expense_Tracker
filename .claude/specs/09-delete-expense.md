# Spec: Delete Expense

## Overview
This step implements the delete flow for user expenses so logged-in users can permanently remove an expense they created. It completes the final CRUD operation in the Spendly roadmap and reinforces ownership checks, confirmation UX, and safe write operations before removing records from the dashboard/profile views.

## Depends on
- Step 03 — Login and Logout (session-based authentication)
- Step 07 — Add Expense (expense records exist)
- Step 08 — Edit Expenses (ownership and expense lookup patterns exist)

## Routes
- `GET /expenses/<id>/delete` — show delete confirmation page for one expense — logged-in
- `POST /expenses/<id>/delete` — delete the expense after confirmation and redirect with flash message — logged-in

## Database changes
No database changes.

## Templates
- **Create:** `templates/delete_expense.html` — confirmation page showing expense details and a danger-style delete action
- **Modify:** `templates/dashboard.html` — add delete action entry point from transaction rows
- **Modify:** `templates/profile.html` — add delete action entry point from transaction rows

## Files to change
- `app.py` — replace delete placeholder route with GET+POST delete flow, auth guard, ownership checks, flash+redirect
- `database/db.py` — add `delete_expense(expense_id, user_id)` helper using parameterised `DELETE`
- `database/queries.py` — include `id` in recent transaction rows so templates can link to edit/delete actions
- `templates/dashboard.html` — add delete link/button per transaction row
- `templates/profile.html` — add delete link/button per transaction row
- `static/css/profile.css` — add styles for row actions and destructive button state using CSS variables

## Files to create
- `templates/delete_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Only the expense owner can view the delete confirmation or perform delete
- If expense is missing, return 404
- If expense belongs to another user, return 403
- Use POST for the actual delete operation; never delete on a GET request
- Include CSRF token validation in the delete confirmation form (same session pattern used in add/edit routes)
- After successful delete, redirect to `url_for("dashboard")` with a success flash message

## Definition of done
- [ ] Logged-out access to `/expenses/<id>/delete` redirects to `/login`
- [ ] Logged-in owner visiting `GET /expenses/<id>/delete` sees a confirmation page with expense summary
- [ ] Submitting `POST /expenses/<id>/delete` with a valid CSRF token deletes exactly one matching row
- [ ] After successful delete, the user is redirected to `/dashboard` and sees a success flash message
- [ ] The deleted expense no longer appears in dashboard/profile recent transaction tables
- [ ] Attempting to delete another user's expense returns 403
- [ ] Attempting to delete a non-existent expense returns 404
- [ ] Submitting delete without a valid CSRF token returns 400 and does not delete data
