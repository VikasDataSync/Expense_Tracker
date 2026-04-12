import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "spendly.db"


def get_db():
    """
    Open a connection to the SQLite database.
    Sets row_factory for dict-like access and enables foreign keys.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_user(name, email, password):
    """
    Creates a new user in the database.
    Returns the new user's ID if successful.
    Raises sqlite3.IntegrityError if the email already exists.
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    """
    Retrieve a user record by their email address.
    Returns the user row if found, otherwise None.
    """
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user


def init_db():
    """
    Create the database tables if they don't exist.
    Safe to call multiple times.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


def seed_db():
    """
    Insert sample data for development.
    Only inserts if no data exists (idempotent).
    """
    conn = get_db()
    cursor = conn.cursor()

    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Insert demo user
    password_hash = generate_password_hash("demo123")
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash)
    )

    # Get the demo user's ID
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",))
    user_id = cursor.fetchone()["id"]

    # Insert 8 sample expenses across categories
    sample_expenses = [
        (500.00, "Food", "2026-04-01", "Breakfast at cafe"),
        (150.50, "Transport", "2026-04-02", "Uber ride to airport"),
        (2500.00, "Bills", "2026-04-03", "Electricity bill"),
        (800.00, "Health", "2026-04-04", "Pharmacy"),
        (1200.00, "Entertainment", "2026-04-05", "Movie tickets and dinner"),
        (3500.00, "Shopping", "2026-04-06", "New shoes"),
        (200.00, "Other", "2026-04-07", "Gift for friend"),
        (350.75, "Food", "2026-04-08", "Grocery shopping"),
    ]

    for amount, category, date, description in sample_expenses:
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )

    conn.commit()
    conn.close()
