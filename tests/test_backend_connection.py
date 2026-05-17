import re
from datetime import datetime, timedelta

import pytest

from app import app as flask_app
from database import db as db_module
from database.db import create_expense, get_db, init_db, seed_db
from database.queries import (
    get_category_distribution,
    get_category_breakdown,
    get_monthly_spend_trend,
    get_recent_transactions,
    get_summary_stats,
    get_top_expenses,
    get_user_by_id,
    get_weekday_spend,
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


def _count_expenses_for_user(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row["total"]
    finally:
        conn.close()


def _expense_exists(expense_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _create_other_user_expense():
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Other User", "other@spendly.com", "hash"),
        )
        other_user_id = cursor.lastrowid
        cursor = conn.execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (other_user_id, 50.0, "Food", "2026-04-11", "Other user expense"),
        )
        conn.commit()
        return other_user_id, cursor.lastrowid
    finally:
        conn.close()


def _set_authenticated_session(client, user_id=None, user_name="Demo User", csrf_token="test-csrf-token"):
    user_id = user_id or _demo_user_id()
    with client.session_transaction() as session:
        session["user_id"] = user_id
        session["user_name"] = user_name
        session["csrf_token"] = csrf_token
    return user_id


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
    assert list(rows[0].keys()) == ["id", "date", "description", "category", "amount"]
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


def test_get_monthly_spend_trend_default_window(test_db):
    trend = get_monthly_spend_trend(_demo_user_id(), months=6)
    assert len(trend) == 6
    april = [item for item in trend if item["month_key"] == "2026-04"][0]
    assert april["total"] == 346.24


def test_get_category_distribution_matches_breakdown(test_db):
    distribution = get_category_distribution(_demo_user_id())
    assert len(distribution) == 7
    assert sum(item["pct"] for item in distribution) == 100


def test_get_weekday_spend_returns_week_order(test_db):
    weekday = get_weekday_spend(_demo_user_id())
    assert [item["day"] for item in weekday] == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    assert round(sum(item["total"] for item in weekday), 2) == 346.24


def test_get_top_expenses_descending_by_amount(test_db):
    rows = get_top_expenses(_demo_user_id(), limit=5)
    assert len(rows) == 5
    amounts = [row["amount"] for row in rows]
    assert amounts == sorted(amounts, reverse=True)
    assert rows[0]["description"] == "Electricity bill"


def test_create_expense_inserts_row(test_db):
    user_id = _demo_user_id()
    before = _count_expenses_for_user(user_id)

    expense_id = create_expense(
        user_id=user_id,
        amount=88.5,
        category="Food",
        date="2026-04-09",
        description="Lunch with team",
    )

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT user_id, amount, category, date, description FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["user_id"] == user_id
    assert row["amount"] == 88.5
    assert row["category"] == "Food"
    assert row["date"] == "2026-04-09"
    assert row["description"] == "Lunch with team"
    assert _count_expenses_for_user(user_id) == before + 1


def test_profile_redirects_when_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_dashboard_redirects_when_unauthenticated(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_add_expense_redirects_when_unauthenticated(client):
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_add_expense_get_shows_form_for_authenticated_user(client):
    _set_authenticated_session(client)

    response = client.get("/expenses/add")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Add expense" in body
    assert "name=\"amount\"" in body
    assert "name=\"category\"" in body
    assert "name=\"date\"" in body
    assert "name=\"csrf_token\"" in body


def test_add_expense_post_valid_data_inserts_and_redirects(client):
    user_id = _set_authenticated_session(client)
    before = _count_expenses_for_user(user_id)

    response = client.post(
        "/expenses/add",
        data={
            "csrf_token": "test-csrf-token",
            "amount": "75.50",
            "category": "Transport",
            "date": "2026-04-10",
            "description": "Cab fare",
        },
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Expense added successfully." in body
    assert _count_expenses_for_user(user_id) == before + 1

    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT amount, category, date, description
            FROM expenses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["amount"] == 75.5
    assert row["category"] == "Transport"
    assert row["date"] == "2026-04-10"
    assert row["description"] == "Cab fare"


def test_add_expense_post_missing_required_fields_shows_error(client):
    user_id = _set_authenticated_session(client)
    before = _count_expenses_for_user(user_id)

    response = client.post(
        "/expenses/add",
        data={
            "csrf_token": "test-csrf-token",
            "amount": "",
            "category": "Food",
            "date": "",
            "description": "Missing required fields",
        },
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Amount, category, and date are required." in body
    assert _count_expenses_for_user(user_id) == before


def test_add_expense_post_non_positive_amount_shows_error(client):
    user_id = _set_authenticated_session(client)
    before = _count_expenses_for_user(user_id)

    response = client.post(
        "/expenses/add",
        data={
            "csrf_token": "test-csrf-token",
            "amount": "0",
            "category": "Food",
            "date": "2026-04-09",
            "description": "Invalid amount",
        },
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Amount must be a number greater than 0." in body
    assert _count_expenses_for_user(user_id) == before


def test_add_expense_post_invalid_date_shows_error(client):
    user_id = _set_authenticated_session(client)
    before = _count_expenses_for_user(user_id)

    response = client.post(
        "/expenses/add",
        data={
            "csrf_token": "test-csrf-token",
            "amount": "12.5",
            "category": "Food",
            "date": "not-a-date",
            "description": "Invalid date",
        },
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Date must be in YYYY-MM-DD format." in body
    assert _count_expenses_for_user(user_id) == before


def test_add_expense_post_invalid_category_shows_error(client):
    user_id = _set_authenticated_session(client)
    before = _count_expenses_for_user(user_id)

    response = client.post(
        "/expenses/add",
        data={
            "csrf_token": "test-csrf-token",
            "amount": "18.0",
            "category": "Crypto",
            "date": "2026-04-09",
            "description": "Invalid category",
        },
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Please select a valid category." in body
    assert _count_expenses_for_user(user_id) == before


def test_add_expense_post_future_date_shows_error(client):
    user_id = _set_authenticated_session(client)
    before = _count_expenses_for_user(user_id)
    future_date = (datetime.now().date() + timedelta(days=1)).isoformat()

    response = client.post(
        "/expenses/add",
        data={
            "csrf_token": "test-csrf-token",
            "amount": "18.0",
            "category": "Food",
            "date": future_date,
            "description": "Future date",
        },
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Date cannot be in the future." in body
    assert _count_expenses_for_user(user_id) == before


def test_add_expense_post_missing_csrf_returns_bad_request(client):
    user_id = _set_authenticated_session(client)
    before = _count_expenses_for_user(user_id)

    response = client.post(
        "/expenses/add",
        data={
            "amount": "25.0",
            "category": "Food",
            "date": "2026-04-09",
            "description": "No csrf",
        },
    )

    assert response.status_code == 400
    assert _count_expenses_for_user(user_id) == before


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


def test_delete_expense_redirects_when_unauthenticated(client):
    response = client.get("/expenses/1/delete")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_delete_expense_get_shows_confirmation_for_owner(client):
    _set_authenticated_session(client)
    expense_id = get_recent_transactions(_demo_user_id(), limit=1)[0]["id"]

    response = client.get(f"/expenses/{expense_id}/delete")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Delete expense" in body
    assert "This action cannot be undone." in body
    assert "name=\"csrf_token\"" in body


def test_delete_expense_post_valid_csrf_deletes_and_redirects(client):
    user_id = _set_authenticated_session(client)
    expense_id = get_recent_transactions(user_id, limit=1)[0]["id"]
    before = _count_expenses_for_user(user_id)

    response = client.post(
        f"/expenses/{expense_id}/delete",
        data={"csrf_token": "test-csrf-token"},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Expense deleted successfully." in body
    assert _count_expenses_for_user(user_id) == before - 1
    assert not _expense_exists(expense_id)


def test_delete_expense_for_other_user_returns_forbidden(client):
    _set_authenticated_session(client)
    _, other_expense_id = _create_other_user_expense()

    response = client.get(f"/expenses/{other_expense_id}/delete")
    assert response.status_code == 403


def test_delete_expense_missing_returns_not_found(client):
    _set_authenticated_session(client)

    response = client.get("/expenses/999999/delete")
    assert response.status_code == 404


def test_delete_expense_post_invalid_csrf_returns_bad_request(client):
    _set_authenticated_session(client)
    expense_id = get_recent_transactions(_demo_user_id(), limit=1)[0]["id"]

    response = client.post(
        f"/expenses/{expense_id}/delete",
        data={"csrf_token": "wrong-token"},
    )

    assert response.status_code == 400
    assert _expense_exists(expense_id)


def test_analytics_redirects_when_unauthenticated(client):
    response = client.get("/analytics")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_analytics_shows_multiple_visualizations(client):
    _set_authenticated_session(client)
    response = client.get("/analytics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Monthly trend" in body
    assert "Category distribution" in body
    assert "Weekday pattern" in body
    assert "Top expenses" in body
    assert "id=\"monthlyChart\"" in body
    assert "id=\"categoryChart\"" in body
    assert "id=\"weekdayChart\"" in body


def test_analytics_malformed_date_falls_back_to_all_time(client):
    _set_authenticated_session(client)
    response = client.get("/analytics?date_from=bad-date&date_to=2026-04-08")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹346.24" in body
    assert ">8<" in body


def test_analytics_range_with_no_expenses_shows_empty_state(client):
    _set_authenticated_session(client)
    response = client.get("/analytics?date_from=2026-05-01&date_to=2026-05-10")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "No analytics data yet." in body


def test_analytics_only_uses_logged_in_user_data(client):
    demo_user_id = _set_authenticated_session(client)

    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Private User", "private@spendly.com", "hash"),
        )
        other_user_id = cursor.lastrowid
        conn.execute(
            """
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (other_user_id, 9999.0, "Shopping", "2026-04-09", "Private high expense"),
        )
        conn.commit()
    finally:
        conn.close()

    response = client.get("/analytics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Private high expense" not in body
    assert "₹9,999.00" not in body
    assert _count_expenses_for_user(demo_user_id) == 8
