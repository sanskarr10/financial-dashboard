"""
Seed script - creates default users and sample financial records
Run with: python seed.py
"""
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.models.database   import init_db, get_connection
from app.models.user_model  import UserModel
from app.models.record_model import RecordModel

def seed():
    print("🌱 Seeding database...\n")

    init_db()

    conn = get_connection()
    conn.execute("DELETE FROM financial_records")
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()

    # ── Users ──────────────────────────────────────────────────────────────────
    admin   = UserModel.create("Alice Admin",   "admin@example.com",   "Password123!", "admin")
    analyst = UserModel.create("Bob Analyst",   "analyst@example.com", "Password123!", "analyst")
    viewer  = UserModel.create("Carol Viewer",  "viewer@example.com",  "Password123!", "viewer")

    print("✅ Users created:")
    print(f"   admin@example.com    (admin)   — id: {admin['id']}")
    print(f"   analyst@example.com  (analyst) — id: {analyst['id']}")
    print(f"   viewer@example.com   (viewer)  — id: {viewer['id']}\n")

    # ── Financial Records ──────────────────────────────────────────────────────
    categories = {
        "income":  ["Salary", "Freelance", "Investment", "Bonus", "Rental"],
        "expense": ["Rent", "Utilities", "Groceries", "Travel", "Software", "Marketing", "Salaries"]
    }

    count = 0
    now   = datetime.now()
    creators = [admin["id"], analyst["id"]]

    for _ in range(60):
        days_ago  = random.randint(0, 364)
        rec_date  = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        type_     = random.choice(["income", "expense", "expense"])
        category  = random.choice(categories[type_])
        amount    = round(random.uniform(100, 9100), 2)

        RecordModel.create(
            amount=amount, type_=type_, category=category,
            date=rec_date, notes=f"Sample {type_} record",
            created_by=random.choice(creators)
        )
        count += 1

    print(f"✅ {count} financial records created\n")
    print("🎉 Seed complete! Start the server with: uvicorn app.main:app --reload")
    print("   Default password for all users: Password123!\n")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"❌ Seed failed: {e}")
        sys.exit(1)
