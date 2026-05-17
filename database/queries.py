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


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        base_query = """
            FROM expenses
            WHERE user_id = ?
        """
        date_filter = ""
        params = [user_id]

        if date_from and date_to:
            date_filter = " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])

        totals_row = conn.execute(
            f"""
            SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transaction_count
            {base_query}
            {date_filter}
            """,
            tuple(params),
        ).fetchone()

        top_category_row = conn.execute(
            f"""
            SELECT category
            {base_query}
            {date_filter}
            GROUP BY category
            ORDER BY SUM(amount) DESC
            LIMIT 1
            """,
            tuple(params),
        ).fetchone()

        return {
            "total_spent": round(float(totals_row["total_spent"]), 2),
            "transaction_count": int(totals_row["transaction_count"]),
            "top_category": top_category_row["category"] if top_category_row else "—",
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()
    try:
        base_query = """
            FROM expenses
            WHERE user_id = ?
        """
        date_filter = ""
        params = [user_id]

        if date_from and date_to:
            date_filter = " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])

        params.append(limit)

        rows = conn.execute(
            f"""
            SELECT id, date, description, category, amount
            {base_query}
            {date_filter}
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "date": row["date"],
                "description": row["description"],
                "category": row["category"],
                "amount": round(float(row["amount"]), 2),
            }
            for row in rows
        ]
    finally:
        conn.close()


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        base_query = """
            FROM expenses
            WHERE user_id = ?
        """
        date_filter = ""
        params = [user_id]

        if date_from and date_to:
            date_filter = " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])

        rows = conn.execute(
            f"""
            SELECT category AS name, SUM(amount) AS amount
            {base_query}
            {date_filter}
            GROUP BY category
            ORDER BY amount DESC
            """,
            tuple(params),
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
