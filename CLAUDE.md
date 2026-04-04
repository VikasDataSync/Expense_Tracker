# CLAUDE.md

This file is the persistent instruction set for Claude Code in this repository. Keep it short, specific, and aligned to the current app state.

## 1. Project Overview and Context

Spendly is a Flask-based expense tracker for learning incremental web app development. The app currently includes public pages and placeholder routes, and students implement the database and authenticated expense flow step by step.

## 2. Architecture

- `app.py` holds the Flask app and route definitions.
- `database/db.py` is the SQLite layer and should expose `get_db()`, `init_db()`, and `seed_db()`.
- `templates/` contains Jinja2 pages shared through `base.html`.
- `static/css/style.css` contains all styling.
- `static/js/main.js` contains frontend behavior.

Keep new code in the appropriate layer: routes in `app.py`, database work in `database/db.py`, presentation in templates, and client behavior in `static/js/main.js`.

## 3. Coding Style and Conventions

- Prefer small, focused functions.
- Keep Flask routes simple and readable.
- Use clear Python names and add type hints where they improve clarity.
- Preserve the existing step-by-step educational style of the project.
- Match the current codebase style instead of introducing unnecessary abstractions.

## 4. Preferred Libraries and Tools

- Use Flask and Jinja2 for the web app.
- Use SQLite for persistence.
- Use vanilla JavaScript and plain CSS.
- Use `pytest` and `pytest-flask` for tests.
- Use only dependencies already listed in `requirements.txt` unless the user explicitly asks for a new one.

## 5. Essential Commands

```bash
python -m pip install -r requirements.txt
python app.py
pytest
```

## 6. Critical Roles and Warnings

- Do not replace the Flask + Jinja2 + SQLite stack with a different framework.
- Do not add third-party libraries unless they are clearly needed and requested.
- Be careful with `database/db.py`; it is the core teaching file for the project setup step.
- Keep placeholder routes aligned with the current step-by-step flow unless you are implementing that step.
- Avoid large refactors that would make the educational progression harder to follow.
- Keep the file under 200 lines and refresh it when the app gains new durable conventions.

## 7. Development Roadmap

| Feature | Status |
| --- | --- |
| Public landing, register, login, terms, privacy pages | Developed |
| SQLite database helper functions | Pending |
| Session-based authentication | Pending |
| Logout and profile routes | Pending |
| Expense CRUD flow | Pending |
| Seed data for development | Pending |

## 8. Important Maintenance Practices

- Keep this file concise and under 200 lines so instructions stay effective.
- Use the word "Important" sparingly, only for genuinely high-priority constraints.
- Treat this as a living document: update it after meaningful feature work and remove stale guidance.
- If project instructions outgrow this file, split durable rules into `.claude/rules/` or module-specific `CLAUDE.md` files.

## Current State

- Landing page, register, login, terms, and privacy pages are implemented.
- Placeholder routes exist for logout, profile, and expense add/edit/delete.
- `database/db.py` currently contains setup notes only.

