import sqlite3
import random
from datetime import datetime, timedelta
from database.db import get_db

def seed_expenses(user_id, count, months):
    # Step 2 — Verify user exists
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        print(f"No user found with id {user_id}.")
        conn.close()
        return

    # Categories and ranges (INR)
    categories = {
        "Food": {"range": (50, 800), "weight": 30, "desc": ["Swiggy order", "Zomato dinner", "Grocery shopping", "Street food", "Cafe coffee"]},
        "Transport": {"range": (20, 500), "weight": 20, "desc": ["Uber ride", "Ola auto", "Petrol refill", "Metro card recharge", "Bus fare"]},
        "Bills": {"range": (200, 3000), "weight": 15, "desc": ["Electricity bill", "Water bill", "Wifi recharge", "Mobile plan", "Rent partial"]},
        "Health": {"range": (100, 2000), "weight": 10, "desc": ["Pharmacy", "Clinic visit", "Medicine", "Health checkup", "Vitamins"]},
        "Entertainment": {"range": (100, 1500), "weight": 10, "desc": ["Movie ticket", "Netflix subscription", "Gaming zone", "Bowling", "Concert ticket"]},
        "Shopping": {"range": (200, 5000), "weight": 10, "desc": ["Amazon order", "Clothes shopping", "Footwear", "Electronic gadget", "Gift item"]},
        "Other": {"range": (50, 1000), "weight": 5, "desc": ["Miscellaneous", "Stationery", "Charity", "Parking fee", "Tips"]},
    }

    cat_list = list(categories.keys())
    weights = [categories[cat]["weight"] for cat in cat_list]

    # Date range calculation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    expenses_to_insert = []
    for _ in range(count):
        category = random.choices(cat_list, weights=weights)[0]
        amount = round(random.uniform(*categories[category]["range"]), 2)
        description = random.choice(categories[category]["desc"])

        # Random date between start and end
        random_days = random.randint(0, (end_date - start_date).days)
        expense_date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

        expenses_to_insert.append((user_id, amount, category, expense_date, description))

    try:
        # Step 3 — Insert in single transaction
        cursor.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses_to_insert
        )
        conn.commit()

        # Step 4 — Confirm
        print(f"Successfully inserted {len(expenses_to_insert)} expenses.")
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print("\nSample of 5 inserted records:")

        # Fetch samples for the specific user
        cursor.execute("SELECT amount, category, date, description FROM expenses WHERE user_id = ? ORDER BY RANDOM() LIMIT 5", (user_id,))
        for row in cursor.fetchall():
            print(f"INR {row['amount']} | {row['category']} | {row['date']} | {row['description']}")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Using parameters provided by user: 2 3 5
    seed_expenses(2, 3, 5)
