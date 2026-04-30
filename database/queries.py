from datetime import datetime
from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None

        created_at = datetime.fromisoformat(row["created_at"])
        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": created_at.strftime("%B %Y"),
        }
    finally:
        conn.close()


def get_summary_stats(user_id):
    conn = get_db()
    try:
        totals_row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transaction_count
            FROM expenses
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        top_category_row = conn.execute(
            """
            SELECT category
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        return {
            "total_spent": round(float(totals_row["total_spent"]), 2),
            "transaction_count": int(totals_row["transaction_count"]),
            "top_category": top_category_row["category"] if top_category_row else "—",
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        return [
            {
                "date": row["date"],
                "description": row["description"],
                "category": row["category"],
                "amount": round(float(row["amount"]), 2),
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_category_breakdown(user_id):
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT category AS name, SUM(amount) AS amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY amount DESC
            """,
            (user_id,),
        ).fetchall()
        if not rows:
            return []

        total = sum(float(row["amount"]) for row in rows)
        if total == 0:
            return []

        breakdown = []
        for row in rows:
            amount = round(float(row["amount"]), 2)
            breakdown.append(
                {
                    "name": row["name"],
                    "amount": amount,
                    "pct": int(round((amount / total) * 100)),
                }
            )

        pct_delta = 100 - sum(item["pct"] for item in breakdown)
        breakdown[0]["pct"] += pct_delta
        return breakdown
    finally:
        conn.close()
