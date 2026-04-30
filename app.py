from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key-for-spendly"


def format_inr(amount):
    return f"₹{amount:,.2f}"


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

    user_id = session["user_id"]
    summary = get_summary_stats(user_id)

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
            "value": str(len(get_category_breakdown(user_id))),
            "change": "Expense categories",
            "trend": "neutral",
        },
    ]

    recent_transactions = []
    for item in get_recent_transactions(user_id):
        recent_transactions.append(
            {
                "date": item["date"],
                "description": item["description"],
                "category": item["category"],
                "category_class": item["category"].lower(),
                "amount": format_inr(item["amount"]),
                "amount_type": "negative",
            }
        )

    category_breakdown = []
    for item in get_category_breakdown(user_id):
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

    return render_template(
        "profile.html",
        user=user,
        summary_stats=get_summary_stats(session["user_id"]),
        recent_transactions=get_recent_transactions(session["user_id"], limit=10),
        category_breakdown=get_category_breakdown(session["user_id"]),
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
