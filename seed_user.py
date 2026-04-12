import random
from datetime import datetime
from werkzeug.security import generate_password_hash
from database.db import get_db

def generate_random_indian_user():
    first_names = ["Aarav", "Vihaan", "Aditya", "Arjun", "Sai", "Ishaan", "Ananya", "Diya", "Myra", "Saanvi"]
    last_names = ["Sharma", "Verma", "Gupta", "Malhotra", "Iyer", "Reddy", "Patel", "Singh", "Chatterjee", "Nair"]

    first = random.choice(first_names)
    last = random.choice(last_names)
    name = f"{first} {last}"

    email_prefix = f"{first.lower()}.{last.lower()}"
    email = f"{email_prefix}{random.randint(10, 999)}@gmail.com"

    return name, email

def seed_user():
    conn = get_db()
    cursor = conn.cursor()

    while True:
        name, email = generate_random_indian_user()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is None:
            break

    password_hash = generate_password_hash("password123")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, created_at)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    print(f"User created successfully:")
    print(f"ID: {user_id}")
    print(f"Name: {name}")
    print(f"Email: {email}")

if __name__ == "__main__":
    seed_user()
