"""Create the tester account and realistic sample finance data (safe to re-run)."""
import os
import random
from datetime import date, datetime, timedelta

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

load_dotenv()
URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
DB_NAME = os.getenv("MONGO_DB", "personal_finance")
USERNAME = "tester"
PASSWORD = "TestFinance2026!"


def seed_database(db):
    rng = random.Random(42)
    account = db.users.find_one({"username": USERNAME})
    if account:
        uid = account["_id"]
        existing = sum(collection.count_documents({"user_id": uid}) for collection in
                       (db.expenses, db.income, db.budgets, db.savings, db.bills, db.financial_goals))
        if existing:
            return False
    else:
        uid = ObjectId()
        db.users.insert_one({"_id": uid, "username": USERNAME, "display_name": "Demo Tester",
                             "password_hash": generate_password_hash(PASSWORD), "created_at": datetime.utcnow()})

    categories = ["Food", "Transport", "Housing", "Utilities", "Shopping", "Health", "Education", "Entertainment", "Travel", "Subscriptions"]
    merchant_titles = {
        "Food": ["Groceries", "Lunch", "Coffee", "Dinner"], "Transport": ["Metro pass", "Cab ride", "Fuel"],
        "Housing": ["Rent", "Home supplies"], "Utilities": ["Electricity bill", "Internet bill", "Mobile recharge"],
        "Shopping": ["Clothing", "Household items"], "Health": ["Pharmacy", "Clinic visit"],
        "Education": ["Online course", "Books"], "Entertainment": ["Movie tickets", "Streaming"],
        "Travel": ["Weekend trip", "Train ticket"], "Subscriptions": ["Cloud storage", "Music plan"],
    }
    payment_modes = ["UPI", "Cash", "Credit Card", "Debit Card", "Bank Transfer", "Wallet"]
    base = date.today().replace(day=1)

    def month_at(offset):
        index = base.year * 12 + base.month - 1 + offset
        return date(index // 12, index % 12 + 1, 1)

    expense_docs = []
    for offset in range(11, -1, -1):
        month_start = month_at(-offset)
        year, month = month_start.year, month_start.month
        last_day = (date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)).day
        items = [("Housing", "Monthly rent", 18000, "Essential")]
        for _ in range(rng.randint(7, 11)):
            cat = rng.choice(categories)
            priority = "Essential" if cat in {"Housing", "Utilities", "Health", "Education"} or rng.random() < 0.48 else "Non-essential"
            amount = rng.randint(120, 4200) if cat not in {"Housing", "Travel"} else rng.randint(600, 6500)
            items.append((cat, rng.choice(merchant_titles[cat]), amount, priority))
        for cat, title, amount, priority in items:
            day = rng.randint(1, last_day)
            when = date(year, month, day).isoformat()
            expense_docs.append({"user_id": uid, "title": title, "category": cat, "amount": float(amount), "date": when,
                                 "payment_mode": rng.choice(payment_modes), "priority": priority,
                                 "note": "Demo transaction — replace with your own entry.",
                                 "created_at": datetime.combine(date(year, month, day), datetime.min.time())})
    if expense_docs:
        db.expenses.insert_many(expense_docs)

    income_docs = []
    for offset in range(11, -1, -1):
        month_start = month_at(-offset)
        income_docs.append({"user_id": uid, "title": "Monthly salary", "source": "Salary", "amount": 65000.0,
                            "date": date(month_start.year, month_start.month, 1).isoformat(),
                            "note": "Demo income", "created_at": datetime.combine(date(month_start.year, month_start.month, 1), datetime.min.time())})
    db.income.insert_many(income_docs)

    this_month = date.today().strftime("%Y-%m")
    for category, amount in [("Overall", 42000), ("Food", 9000), ("Transport", 5000), ("Shopping", 6000), ("Entertainment", 3500)]:
        db.budgets.insert_one({"user_id": uid, "month": this_month, "category": category, "amount": float(amount), "created_at": datetime.utcnow()})

    for doc in [
        {"user_id": uid, "title": "Emergency fund", "amount": 10000.0, "date": date.today().isoformat(), "note": "Demo savings"},
        {"user_id": uid, "title": "Travel fund", "amount": 5000.0, "date": date.today().isoformat(), "note": "Demo savings"},
    ]:
        doc["created_at"] = datetime.utcnow()
        db.savings.insert_one(doc)

    for title, amount, due, status in [
        ("Electricity", 1850, date.today() + timedelta(days=5), "Upcoming"),
        ("Internet", 999, date.today() + timedelta(days=12), "Upcoming"),
        ("Mobile plan", 599, date.today() - timedelta(days=3), "Paid"),
    ]:
        db.bills.insert_one({"user_id": uid, "title": title, "amount": float(amount), "due_date": due.isoformat(),
                             "status": status, "created_at": datetime.utcnow()})

    for title, target, saved, deadline in [
        ("Emergency fund", 150000, 45000, date.today() + timedelta(days=300)),
        ("New laptop", 90000, 27000, date.today() + timedelta(days=180)),
        ("Vacation", 60000, 12000, date.today() + timedelta(days=240)),
    ]:
        db.financial_goals.insert_one({"user_id": uid, "title": title, "target_amount": float(target),
                                       "saved_amount": float(saved), "deadline": deadline.isoformat(), "created_at": datetime.utcnow()})

    try:
        db.users.create_index("username", unique=True)
        for collection in (db.expenses, db.income, db.budgets, db.savings, db.bills, db.financial_goals):
            collection.create_index([("user_id", 1), ("date", -1)]) if collection.name in ("expenses", "income", "savings") else collection.create_index([("user_id", 1)])
    except Exception:
        pass
    return True


if __name__ == "__main__":
    client = MongoClient(URI, serverSelectionTimeoutMS=3000)
    db = client[DB_NAME]
    client.admin.command("ping")
    seeded = seed_database(db)
    if seeded:
        print("Seed complete.")
        print(f"MongoDB database: {DB_NAME}")
        print(f"Username: {USERNAME} | Password: {PASSWORD}")
    else:
        print("Demo account/data already exists; no duplicate data added.")
        print(f"Username: {USERNAME} | Password: {PASSWORD}")
    client.close()
