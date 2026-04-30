import re

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


def test_get_recent_transactions_with_expenses(test_db):
    rows = get_recent_transactions(_demo_user_id())
    assert len(rows) == 8
    assert list(rows[0].keys()) == ["date", "description", "category", "amount"]
    assert rows[0]["date"] == "2026-04-08"
    assert rows[-1]["date"] == "2026-04-01"


def test_get_recent_transactions_without_expenses(test_db):
    user_id = _create_user_without_expenses()
    assert get_recent_transactions(user_id) == []


def test_get_category_breakdown_with_expenses(test_db):
    breakdown = get_category_breakdown(_demo_user_id())
    amounts = [item["amount"] for item in breakdown]
    assert len(breakdown) == 7
    assert amounts == sorted(amounts, reverse=True)
    assert sum(item["pct"] for item in breakdown) == 100


def test_get_category_breakdown_without_expenses(test_db):
    user_id = _create_user_without_expenses()
    assert get_category_breakdown(user_id) == []


def test_profile_redirects_when_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


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
