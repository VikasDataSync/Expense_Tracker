import re
from datetime import datetime, timedelta

import pytest

from app import app as flask_app
from database import db as db_module
from database.db import get_db, init_db, seed_db
from database.queries import (
    get_category_breakdown,
    get_recent_transactions,
    get_summary_stats,
    get_user_by_id,
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    db_path = tmp_path / "spendly_test.db"
    monkeypatch.setattr(db_module, "DB_NAME", str(db_path))
    init_db()
    seed_db()
    yield db_path


@pytest.fixture
def client(test_db):
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as test_client:
        yield test_client


def _demo_user_id():
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            ("demo@spendly.com",),
        ).fetchone()
        return row["id"]
    finally:
        conn.close()


def _create_user_without_expenses():
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("New User", "new@spendly.com", "hash"),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def test_get_user_by_id_valid(test_db):
    user = get_user_by_id(_demo_user_id())
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    assert re.match(r"^[A-Za-z]+ \d{4}$", user["member_since"])


def test_get_user_by_id_not_found(test_db):
    assert get_user_by_id(999999) is None


def test_get_summary_stats_with_expenses(test_db):
    stats = get_summary_stats(_demo_user_id())
    assert stats == {
        "total_spent": 346.24,
        "transaction_count": 8,
        "top_category": "Bills",
    }


def test_get_summary_stats_without_expenses(test_db):
    user_id = _create_user_without_expenses()
    stats = get_summary_stats(user_id)
    assert stats == {
        "total_spent": 0.0,
        "transaction_count": 0,
        "top_category": "—",
    }


def test_get_summary_stats_with_date_range(test_db):
    stats = get_summary_stats(_demo_user_id(), date_from="2026-04-03", date_to="2026-04-04")
    assert stats == {
        "total_spent": 148.74,
        "transaction_count": 2,
        "top_category": "Bills",
    }


def test_get_recent_transactions_with_expenses(test_db):
    rows = get_recent_transactions(_demo_user_id())
    assert len(rows) == 8
    assert list(rows[0].keys()) == ["date", "description", "category", "amount"]
    assert rows[0]["date"] == "2026-04-08"
    assert rows[-1]["date"] == "2026-04-01"


def test_get_recent_transactions_without_expenses(test_db):
    user_id = _create_user_without_expenses()
    assert get_recent_transactions(user_id) == []


def test_get_recent_transactions_with_date_range(test_db):
    rows = get_recent_transactions(_demo_user_id(), date_from="2026-04-03", date_to="2026-04-04")
    assert [row["date"] for row in rows] == ["2026-04-04", "2026-04-03"]


def test_get_category_breakdown_with_expenses(test_db):
    breakdown = get_category_breakdown(_demo_user_id())
    amounts = [item["amount"] for item in breakdown]
    assert len(breakdown) == 7
    assert amounts == sorted(amounts, reverse=True)
    assert sum(item["pct"] for item in breakdown) == 100


def test_get_category_breakdown_without_expenses(test_db):
    user_id = _create_user_without_expenses()
    assert get_category_breakdown(user_id) == []


def test_get_category_breakdown_with_date_range(test_db):
    breakdown = get_category_breakdown(_demo_user_id(), date_from="2026-04-03", date_to="2026-04-04")
    assert breakdown == [
        {"name": "Bills", "amount": 120.0, "pct": 81},
        {"name": "Health", "amount": 28.74, "pct": 19},
    ]


def test_profile_redirects_when_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_dashboard_redirects_when_unauthenticated(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_dashboard_shows_filter_bar(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/dashboard")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Filter by date" in body
    assert "This Month" in body
    assert "Last 3 Months" in body
    assert "Last 6 Months" in body
    assert "name=\"date_from\"" in body
    assert "name=\"date_to\"" in body


def test_dashboard_custom_date_range_filters_sections(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/dashboard?date_from=2026-04-03&date_to=2026-04-04")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹148.74" in body
    assert ">2<" in body
    assert "Bills" in body
    assert "Health" in body
    assert "2026-04-08" not in body


def test_dashboard_reversed_date_range_flashes_and_falls_back(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/dashboard?date_from=2026-04-10&date_to=2026-04-01")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Start date must be before end date." in body
    assert "₹346.24" in body
    assert ">8<" in body


def test_profile_authenticated_seed_user(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "₹" in body
    assert "₹346.24" in body
    assert ">8<" in body
    assert "Bills" in body
    assert body.index("2026-04-08") < body.index("2026-04-01")

    for category in [
        "Food",
        "Transport",
        "Bills",
        "Health",
        "Entertainment",
        "Shopping",
        "Other",
    ]:
        assert category in body


def test_profile_authenticated_new_user_empty_stats(client):
    user_id = _create_user_without_expenses()
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["user_name"] = "New User"

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹0.00" in body
    assert "No transactions yet." in body
    assert "No category data yet." in body


def test_profile_custom_date_range_filters_all_sections(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/profile?date_from=2026-04-03&date_to=2026-04-04")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹148.74" in body
    assert ">2<" in body
    assert "Bills" in body
    assert "Health" in body
    assert "2026-04-04" in body
    assert "2026-04-03" in body
    assert "2026-04-08" not in body


def test_profile_reversed_date_range_flashes_and_falls_back(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/profile?date_from=2026-04-10&date_to=2026-04-01")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Start date must be before end date." in body
    assert "₹346.24" in body
    assert ">8<" in body


def test_profile_malformed_date_falls_back_to_all_time(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/profile?date_from=not-a-date&date_to=2026-04-08")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹346.24" in body
    assert ">8<" in body


def test_profile_range_with_no_expenses_shows_empty_state(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/profile?date_from=2026-05-01&date_to=2026-05-10")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹0.00" in body
    assert "No transactions yet." in body
    assert "No category data yet." in body


def test_profile_preset_links_use_calculated_route_dates(client):
    with client.session_transaction() as session:
        session["user_id"] = _demo_user_id()
        session["user_name"] = "Demo User"

    response = client.get("/profile")
    body = response.get_data(as_text=True)

    today = datetime.now().date()
    this_month_from = today.replace(day=1).isoformat()
    last_3_months_from = (today - timedelta(days=90)).isoformat()
    last_6_months_from = (today - timedelta(days=180)).isoformat()
    today_iso = today.isoformat()

    assert response.status_code == 200
    assert f"/profile?date_from={this_month_from}&amp;date_to={today_iso}" in body
    assert f"/profile?date_from={last_3_months_from}&amp;date_to={today_iso}" in body
    assert f"/profile?date_from={last_6_months_from}&amp;date_to={today_iso}" in body
