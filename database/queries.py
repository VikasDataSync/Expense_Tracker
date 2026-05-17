from datetime import date, datetime
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


def _month_start_with_offset(month_start, offset):
    absolute_month = (month_start.year * 12 + month_start.month - 1) + offset
    year = absolute_month // 12
    month = absolute_month % 12 + 1
    return date(year, month, 1)


def get_monthly_spend_trend(user_id, date_from=None, date_to=None, months=6):
    conn = get_db()
    try:
        params = [user_id]
        date_filter = ""
        if date_from and date_to:
            date_filter = " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])

        rows = conn.execute(
            f"""
            SELECT strftime('%Y-%m', date) AS month_key, COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = ?
            {date_filter}
            GROUP BY month_key
            ORDER BY month_key
            """,
            tuple(params),
        ).fetchall()

        totals_by_month = {row["month_key"]: round(float(row["total"]), 2) for row in rows}

        if date_from and date_to:
            start_month = datetime.strptime(date_from, "%Y-%m-%d").date().replace(day=1)
            end_month = datetime.strptime(date_to, "%Y-%m-%d").date().replace(day=1)
            month_starts = []
            step = 0
            while True:
                current = _month_start_with_offset(start_month, step)
                if current > end_month:
                    break
                month_starts.append(current)
                step += 1
        else:
            current_month = date.today().replace(day=1)
            month_starts = [
                _month_start_with_offset(current_month, offset)
                for offset in range(-(months - 1), 1)
            ]

        return [
            {
                "month_key": month_start.strftime("%Y-%m"),
                "month": month_start.strftime("%b %Y"),
                "total": totals_by_month.get(month_start.strftime("%Y-%m"), 0.0),
            }
            for month_start in month_starts
        ]
    finally:
        conn.close()


def get_category_distribution(user_id, date_from=None, date_to=None):
    return get_category_breakdown(user_id, date_from=date_from, date_to=date_to)


def get_weekday_spend(user_id, date_from=None, date_to=None):
    conn = get_db()
    try:
        params = [user_id]
        date_filter = ""
        if date_from and date_to:
            date_filter = " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])

        rows = conn.execute(
            f"""
            SELECT strftime('%w', date) AS weekday_key, COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = ?
            {date_filter}
            GROUP BY weekday_key
            """,
            tuple(params),
        ).fetchall()

        totals = {row["weekday_key"]: round(float(row["total"]), 2) for row in rows}
        ordered = [
            ("1", "Mon"),
            ("2", "Tue"),
            ("3", "Wed"),
            ("4", "Thu"),
            ("5", "Fri"),
            ("6", "Sat"),
            ("0", "Sun"),
        ]
        return [{"day": label, "total": totals.get(key, 0.0)} for key, label in ordered]
    finally:
        conn.close()


def get_top_expenses(user_id, limit=5, date_from=None, date_to=None):
    conn = get_db()
    try:
        params = [user_id]
        date_filter = ""
        if date_from and date_to:
            date_filter = " AND date BETWEEN ? AND ?"
            params.extend([date_from, date_to])
        params.append(limit)

        rows = conn.execute(
            f"""
            SELECT id, date, category, description, amount
            FROM expenses
            WHERE user_id = ?
            {date_filter}
            ORDER BY amount DESC, date DESC, id DESC
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "date": row["date"],
                "category": row["category"],
                "description": row["description"],
                "amount": round(float(row["amount"]), 2),
            }
            for row in rows
        ]
    finally:
        conn.close()
