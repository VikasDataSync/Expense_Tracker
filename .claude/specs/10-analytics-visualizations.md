# Spec: Analytics Visualizations

## Overview
This step replaces the current “coming soon” analytics placeholder with a real, logged-in analytics experience that shows multiple spending visualizations from existing expense data. At this stage of the roadmap, users already create/edit/delete expenses and filter by date, so analytics now turns that raw history into clear trends (monthly spending), composition (category share), and day-level patterns to help users understand where and when they spend.

## Depends on
- Step 03 — Login and Logout (session auth guard)
- Step 05 — Backend connection (query helpers and profile data wiring)
- Step 06 — Date filtering (query-string date range behavior)
- Step 07 — Add Expense
- Step 08 — Edit Expenses
- Step 09 — Delete Expense

## Routes
No new routes.

## Database changes
No database changes.

## Templates
- **Create:** No new templates.
- **Modify:** `templates/analytics.html` — replace placeholder card with analytics dashboard sections and chart containers (monthly trend, category distribution, weekday spending, top expenses table), plus date filter controls.

## Files to change
- `app.py` — update existing `analytics()` route to:
  - enforce logged-in access (already present),
  - parse/validate date filters (reuse existing filter helper pattern),
  - fetch analytics datasets from query helpers,
  - pass chart-ready data structures to template.
- `database/queries.py` — add analytics query helpers using parameterized SQL:
  - monthly totals for last N months (or filtered period),
  - category totals and percentages,
  - weekday totals,
  - top expenses list.
- `templates/analytics.html` — render multiple visualization blocks and empty-state messaging.
- `static/css/style.css` — add analytics page styling using existing design tokens and layout patterns.
- `static/js/main.js` — add client-side rendering logic for lightweight visualizations (no external chart library), consuming JSON data embedded by the template.

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Keep analytics on `GET /analytics`; drive filters via query params (`date_from`, `date_to`) only
- Reuse server-side date validation behavior already used in dashboard/profile (malformed or reversed ranges fall back safely)
- Do not embed SQL in route handlers; all analytics SQL must live in `database/queries.py`
- Support empty datasets gracefully (show clear empty-state text instead of broken visuals)
- Keep visualization rendering dependency-free (vanilla JS + HTML/CSS/SVG/canvas already available in browser)
- Display all currency values with ₹ formatting

## Definition of done
- [ ] Logged-out user visiting `/analytics` is redirected to `/login`
- [ ] Logged-in user visiting `/analytics` sees multiple visualizations (at minimum: monthly trend, category distribution, weekday pattern)
- [ ] Analytics values are generated from the logged-in user’s own expenses only
- [ ] Date filters on analytics correctly update all visualizations together
- [ ] Malformed or reversed date ranges do not crash the page and fall back to a safe default
- [ ] A user with no expenses sees an empty-state analytics page with no runtime errors
- [ ] Top-expense section lists highest individual expenses in descending amount order
- [ ] All SQL used for analytics is parameterized and implemented in query helper functions
- [ ] No new pip packages are added
