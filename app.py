from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from database.db import (
    get_db,
    init_db,
    seed_db,
    create_user,
    get_user_by_email,
    create_expense,
    get_expense_by_id,
    update_expense,
    delete_expense as delete_expense_db,
)
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)
import sqlite3
import secrets
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "dev-secret-key-for-spendly"

EXPENSE_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


@app.template_filter("format_date_iso")
def format_date_iso(date_obj):
    """Format a date object as ISO string (YYYY-MM-DD) for use in URLs."""
    return date_obj.strftime("%Y-%m-%d")


def format_inr(amount):
    return f"₹{amount:,.2f}"


def parse_date(value):
    """Parse an ISO date string (YYYY-MM-DD) to a date object."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def get_date_filter_context(args):
    """Build validated date filter values and UI state from query parameters."""
    date_from_raw = args.get("date_from")
    date_to_raw = args.get("date_to")

    date_from = parse_date(date_from_raw) if date_from_raw else None
    date_to = parse_date(date_to_raw) if date_to_raw else None

    # Filter only applies when both bounds are valid.
    if not (date_from and date_to):
        date_from = None
        date_to = None

    error_message = None
    if date_from is not None and date_to is not None and date_from > date_to:
        error_message = "Start date must be before end date."
        date_from = None
        date_to = None

    today = datetime.now().date()
    first_of_month = today.replace(day=1)
    three_months_ago = today - timedelta(days=90)
    six_months_ago = today - timedelta(days=180)

    is_all_time = date_from is None and date_to is None
    is_this_month = date_from == first_of_month and date_to == today
    is_last_3_months = date_from == three_months_ago and date_to == today
    is_last_6_months = date_from == six_months_ago and date_to == today
    is_custom_range = not is_all_time and not (is_this_month or is_last_3_months or is_last_6_months)

    return {
        "error_message": error_message,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "today_iso": today.isoformat(),
        "this_month_from": first_of_month.isoformat(),
        "last_3_months_from": three_months_ago.isoformat(),
        "last_6_months_from": six_months_ago.isoformat(),
        "is_all_time": is_all_time,
        "is_this_month": is_this_month,
        "is_last_3_months": is_last_3_months,
        "is_last_6_months": is_last_6_months,
        "is_custom_range": is_custom_range,
    }


def validate_expense_form(form_data, today):
    if not form_data["amount"] or not form_data["category"] or not form_data["date"]:
        return None, "Amount, category, and date are required."

    try:
        amount = float(form_data["amount"])
    except ValueError:
        return None, "Amount must be a number greater than 0."

    if amount <= 0:
        return None, "Amount must be a number greater than 0."

    if form_data["category"] not in EXPENSE_CATEGORIES:
        return None, "Please select a valid category."

    expense_date = parse_date(form_data["date"])
    if expense_date is None:
        return None, "Date must be in YYYY-MM-DD format."

    if expense_date > today:
        return None, "Date cannot be in the future."

    return amount, None


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.")

        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            return render_template("register.html", error="An account with this email already exists.")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    filter_context = get_date_filter_context(request.args)
    if filter_context["error_message"]:
        flash(filter_context["error_message"], "error")

    date_from = filter_context["date_from"]
    date_to = filter_context["date_to"]
    user_id = session["user_id"]
    summary = get_summary_stats(user_id, date_from=date_from, date_to=date_to)
    categories = get_category_breakdown(user_id, date_from=date_from, date_to=date_to)

    summary_stats = [
        {
            "label": "Total spent",
            "value": format_inr(summary["total_spent"]),
            "change": "All-time spending",
            "trend": "neutral",
        },
        {
            "label": "Transactions",
            "value": str(summary["transaction_count"]),
            "change": "Recorded expenses",
            "trend": "neutral",
        },
        {
            "label": "Top category",
            "value": summary["top_category"],
            "change": "Highest total spend",
            "trend": "neutral",
        },
        {
            "label": "Categories",
            "value": str(len(categories)),
            "change": "Expense categories",
            "trend": "neutral",
        },
    ]

    recent_transactions = []
    for item in get_recent_transactions(user_id, date_from=date_from, date_to=date_to):
        recent_transactions.append(
            {
                "id": item["id"],
                "date": item["date"],
                "description": item["description"],
                "category": item["category"],
                "category_class": item["category"].lower(),
                "amount": format_inr(item["amount"]),
                "amount_type": "negative",
            }
        )

    category_breakdown = []
    for item in categories:
        if item["pct"] >= 33:
            bar_class = "bar-fill-39"
        elif item["pct"] >= 24:
            bar_class = "bar-fill-27"
        elif item["pct"] >= 17:
            bar_class = "bar-fill-20"
        else:
            bar_class = "bar-fill-14"

        category_breakdown.append(
            {
                "name": item["name"],
                "total": format_inr(item["amount"]),
                "share": f"{item['pct']}%",
                "bar_class": bar_class,
            }
        )

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name", "User"),
        summary_stats=summary_stats,
        recent_transactions=recent_transactions,
        category_breakdown=category_breakdown,
        **filter_context,
    )


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('landing'))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    session["user_name"] = user["name"]

    filter_context = get_date_filter_context(request.args)
    if filter_context["error_message"]:
        flash(filter_context["error_message"], "error")

    user_id = session["user_id"]

    return render_template(
        "profile.html",
        user=user,
        summary_stats=get_summary_stats(user_id, filter_context["date_from"], filter_context["date_to"]),
        recent_transactions=get_recent_transactions(
            user_id, limit=10, date_from=filter_context["date_from"], date_to=filter_context["date_to"]
        ),
        category_breakdown=get_category_breakdown(
            user_id, date_from=filter_context["date_from"], date_to=filter_context["date_to"]
        ),
        **filter_context,
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    return render_template("analytics.html")


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    today = datetime.now().date()
    today_iso = today.isoformat()
    form_data = {
        "amount": "",
        "category": "",
        "date": today_iso,
        "description": "",
    }
    csrf_token = session.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(16)
        session["csrf_token"] = csrf_token

    error = None
    if request.method == "GET":
        csrf_token = secrets.token_hex(16)
        session["csrf_token"] = csrf_token
    else:
        form_token = request.form.get("csrf_token")
        if not form_token or form_token != session.get("csrf_token"):
            abort(400)

        form_data["amount"] = request.form.get("amount", "").strip()
        form_data["category"] = request.form.get("category", "").strip()
        form_data["date"] = request.form.get("date", "").strip()
        form_data["description"] = request.form.get("description", "").strip()

        amount, error = validate_expense_form(form_data, today)
        if error is None:
            create_expense(
                session["user_id"],
                amount,
                form_data["category"],
                form_data["date"],
                form_data["description"] or None,
            )
            flash("Expense added successfully.", "success")
            return redirect(url_for("dashboard"))

    return render_template(
        "add_expense.html",
        categories=EXPENSE_CATEGORIES,
        form_data=form_data,
        error=error,
        today_iso=today_iso,
        csrf_token=csrf_token,
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Load the expense
    expense = get_expense_by_id(id)
    if expense is None:
        abort(404)

    # Check ownership
    if expense["user_id"] != session["user_id"]:
        abort(403)

    today = datetime.now().date()
    today_iso = today.isoformat()
    
    form_data = {
        "amount": "",
        "category": "",
        "date": today_iso,
        "description": "",
    }
    csrf_token = session.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(16)
        session["csrf_token"] = csrf_token

    error = None
    if request.method == "GET":
        csrf_token = secrets.token_hex(16)
        session["csrf_token"] = csrf_token
        form_data = {
            "amount": str(expense["amount"]),
            "category": expense["category"],
            "date": expense["date"],
            "description": expense["description"] or "",
        }
    else:
        form_token = request.form.get("csrf_token")
        if not form_token or form_token != session.get("csrf_token"):
            abort(400)

        form_data["amount"] = request.form.get("amount", "").strip()
        form_data["category"] = request.form.get("category", "").strip()
        form_data["date"] = request.form.get("date", "").strip()
        form_data["description"] = request.form.get("description", "").strip()

        amount, error = validate_expense_form(form_data, today)
        if error is None:
            success = update_expense(
                id,
                session["user_id"],
                amount,
                form_data["category"],
                form_data["date"],
                form_data["description"] or None,
            )
            if success:
                flash("Expense updated successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                abort(403)

    return render_template(
        "edit_expense.html",
        categories=EXPENSE_CATEGORIES,
        form_data=form_data,
        error=error,
        today_iso=today_iso,
        csrf_token=csrf_token,
        expense_id=id,
    )


@app.route("/expenses/<int:id>/delete", methods=["GET", "POST"])
def delete_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id)
    if expense is None:
        abort(404)

    if expense["user_id"] != session["user_id"]:
        abort(403)

    csrf_token = session.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(16)
        session["csrf_token"] = csrf_token

    if request.method == "GET":
        csrf_token = secrets.token_hex(16)
        session["csrf_token"] = csrf_token
        return render_template(
            "delete_expense.html",
            expense=expense,
            csrf_token=csrf_token,
        )

    form_token = request.form.get("csrf_token")
    if not form_token or form_token != session.get("csrf_token"):
        abort(400)

    if not delete_expense_db(id, session["user_id"]):
        abort(404)

    flash("Expense deleted successfully.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
