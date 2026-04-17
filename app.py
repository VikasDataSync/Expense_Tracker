from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "dev-secret-key-for-spendly"


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

    summary_stats = [
        {
            "label": "This month spending",
            "value": "₹18,240",
            "change": "+8% vs last month",
            "trend": "negative",
        },
        {
            "label": "Transactions",
            "value": "34",
            "change": "6 more than last month",
            "trend": "neutral",
        },
        {
            "label": "Budget left",
            "value": "₹6,760",
            "change": "43% remaining",
            "trend": "positive",
        },
        {
            "label": "Top category",
            "value": "Food",
            "change": "₹7,120 total",
            "trend": "neutral",
        },
    ]

    recent_transactions = [
        {
            "date": "17 Apr 2026",
            "description": "Swiggy dinner order",
            "category": "Food",
            "category_class": "food",
            "amount": "-₹740",
            "amount_type": "negative",
        },
        {
            "date": "16 Apr 2026",
            "description": "Uber to office",
            "category": "Transport",
            "category_class": "transport",
            "amount": "-₹320",
            "amount_type": "negative",
        },
        {
            "date": "15 Apr 2026",
            "description": "Electricity bill",
            "category": "Bills",
            "category_class": "bills",
            "amount": "-₹2,450",
            "amount_type": "negative",
        },
        {
            "date": "14 Apr 2026",
            "description": "Headphones purchase",
            "category": "Shopping",
            "category_class": "shopping",
            "amount": "-₹1,999",
            "amount_type": "negative",
        },
        {
            "date": "13 Apr 2026",
            "description": "Refund from merchant",
            "category": "Other",
            "category_class": "other",
            "amount": "+₹430",
            "amount_type": "positive",
        },
    ]

    category_breakdown = [
        {
            "name": "Food",
            "total": "₹7,120",
            "share": "39%",
            "bar_class": "bar-fill-39",
        },
        {
            "name": "Bills",
            "total": "₹4,980",
            "share": "27%",
            "bar_class": "bar-fill-27",
        },
        {
            "name": "Shopping",
            "total": "₹3,620",
            "share": "20%",
            "bar_class": "bar-fill-20",
        },
        {
            "name": "Transport",
            "total": "₹2,520",
            "share": "14%",
            "bar_class": "bar-fill-14",
        },
    ]

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
    return "Profile page — coming in Step 4"


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
