"""FinTrack: Flask + MongoDB personal finance tracker."""
from __future__ import annotations

import csv
import io
import math
import os
import re
from datetime import date, datetime, timezone
from functools import wraps
from collections import defaultdict

from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "change-this-development-secret-before-deploying"),
    MONGO_URI=os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/"),
    MONGO_DB=os.getenv("MONGO_DB", "personal_finance"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def _connect_database():
    """Connect to configured MongoDB server, or fallback to an in-memory mock."""
    try:
        c = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=2500, connectTimeoutMS=2500)
        c.admin.command("ping")
        return c, c[app.config["MONGO_DB"]]
    except Exception:
        try:
            import mongomock
            from seed_demo import seed_database
            c = mongomock.MongoClient()
            d = c[app.config["MONGO_DB"]]
            seed_database(d)
            return c, d
        except Exception:
            c = MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=2500, connectTimeoutMS=2500)
            return c, c[app.config["MONGO_DB"]]


client, db = _connect_database()
users = db.users
expenses = db.expenses
income = db.income
budgets = db.budgets
savings = db.savings
bills = db.bills
goals = db.financial_goals

CATEGORIES = ["Food", "Transport", "Housing", "Utilities", "Shopping", "Health", "Education", "Entertainment", "Travel", "Subscriptions", "Other"]
PAYMENT_MODES = ["UPI", "Cash", "Credit Card", "Debit Card", "Bank Transfer", "Wallet", "Other"]


def user_id() -> ObjectId:
    raw_id = session.get("user_id")
    if not raw_id or not ObjectId.is_valid(raw_id):
        session.clear()
        raise ValueError("Invalid user session.")
    return ObjectId(raw_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session or not ObjectId.is_valid(session.get("user_id", "")):
            session.clear()
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def money(value, field="Amount") -> float:
    try:
        result = round(float(value), 2)
        if not math.isfinite(result) or result <= 0 or result > 1_000_000_000:
            raise ValueError
        return result
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number greater than zero.")


def money_non_negative(value, field="Amount") -> float:
    try:
        val = 0.0 if value is None or str(value).strip() == "" else float(value)
        result = round(val, 2)
        if not math.isfinite(result) or result < 0 or result > 1_000_000_000:
            raise ValueError
        return result
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number greater than or equal to zero.")


def valid_date(value, field="Date") -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"Please enter a valid {field.lower()}.")


def owner_filter(extra=None):
    result = {"user_id": user_id()}
    if extra:
        result.update(extra)
    return result


def aggregate_totals(collection, query):
    rows = collection.find(query, {"amount": 1})
    return round(sum(float(x.get("amount", 0) or 0) for x in rows), 2)


def get_category_breakdown(uid: ObjectId):
    """Safely return breakdown of expenses by category with aggregation fallback."""
    try:
        return list(expenses.aggregate([
            {"$match": {"user_id": uid}},
            {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
            {"$sort": {"total": -1}},
        ]))
    except Exception:
        totals = defaultdict(float)
        for row in expenses.find({"user_id": uid}, {"category": 1, "amount": 1}):
            totals[row.get("category", "Other")] += float(row.get("amount", 0) or 0)
        sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        return [{"_id": k, "total": round(v, 2)} for k, v in sorted_items]


def expense_filters(args):
    query = owner_filter()
    category = args.get("category", "").strip()
    priority = args.get("priority", "").strip()
    payment = args.get("payment", "").strip()
    start = args.get("start", "").strip()
    end = args.get("end", "").strip()
    search = args.get("q", "").strip()
    if category in CATEGORIES:
        query["category"] = category
    if priority in ("Essential", "Non-essential"):
        query["priority"] = priority
    if payment in PAYMENT_MODES:
        query["payment_mode"] = payment
    date_range = {}
    if start:
        try:
            date_range["$gte"] = valid_date(start, "Start date")
        except ValueError:
            pass
    if end:
        try:
            date_range["$lte"] = valid_date(end, "End date")
        except ValueError:
            pass
    if date_range:
        query["date"] = date_range
    if search:
        safe_pattern = re.compile(re.escape(search[:80]), re.IGNORECASE)
        query["$or"] = [{"title": safe_pattern}, {"note": safe_pattern}]
    return query


@app.context_processor
def inject_globals():
    return {
        "categories": CATEGORIES,
        "payment_modes": PAYMENT_MODES,
        "current_user": session.get("username"),
        "today": date.today().isoformat()
    }


@app.route("/health")
def health():
    try:
        client.admin.command("ping")
        return {"status": "ok", "mongodb": "connected", "database": app.config["MONGO_DB"]}
    except PyMongoError as exc:
        return {"status": "error", "mongodb": "disconnected", "message": str(exc)}, 503


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        try:
            account = users.find_one({"username": username})
        except PyMongoError:
            flash("MongoDB is not reachable. Start MongoDB Server and try again.", "error")
            return render_template("login.html")
        if account and check_password_hash(account.get("password_hash", ""), password):
            session.clear()
            session["user_id"] = str(account["_id"])
            session["username"] = account["username"]
            flash(f"Welcome back, {account.get('display_name', username)}!", "success")
            target = request.args.get("next", "")
            return redirect(target if target.startswith("/") and not target.startswith("//") else url_for("index"))
        flash("Username or password is incorrect.", "error")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("display_name", "").strip()[:80]
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if not name or len(username) < 3 or len(password) < 8:
            flash("Enter your name, a username (at least 3 characters), and password (at least 8 characters).", "error")
        elif not re.match(r"^[a-z0-9_.-]+$", username):
            flash("Username can only contain letters, numbers, dots, hyphens, and underscores.", "error")
        else:
            try:
                if users.find_one({"username": username}):
                    flash("That username is already taken.", "error")
                else:
                    now = datetime.now(timezone.utc)
                    result = users.insert_one({
                        "username": username,
                        "display_name": name,
                        "password_hash": generate_password_hash(password),
                        "created_at": now
                    })
                    session["user_id"] = str(result.inserted_id)
                    session["username"] = username
                    flash("Your account is ready. Start by recording an expense or income.", "success")
                    return redirect(url_for("index"))
            except PyMongoError:
                flash("MongoDB is not reachable. Start MongoDB Server and try again.", "error")
    return render_template("signup.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    uid = user_id()
    inc = aggregate_totals(income, {"user_id": uid})
    exp = aggregate_totals(expenses, {"user_id": uid})
    category_data = get_category_breakdown(uid)
    recent = list(expenses.find({"user_id": uid}).sort([("date", -1), ("created_at", -1)]).limit(6))
    month = date.today().strftime("%Y-%m")
    month_regex = re.compile(r"^" + re.escape(month))
    month_spend = aggregate_totals(expenses, {"user_id": uid, "date": month_regex})
    month_budget = aggregate_totals(budgets, {"user_id": uid, "month": month})
    month_income = aggregate_totals(income, {"user_id": uid, "date": month_regex})
    return render_template("index.html",
                           income_total=inc,
                           expense_total=exp,
                           balance=round(inc - exp, 2),
                           category_data=category_data,
                           recent_expenses=recent,
                           month_spend=month_spend,
                           month_budget=month_budget,
                           month_income=month_income)


@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()[:120]
            if not title:
                raise ValueError("Please enter an expense title.")
            category = request.form.get("category", "Other")
            if category not in CATEGORIES:
                category = "Other"
            priority = request.form.get("priority", "Essential")
            if priority not in ("Essential", "Non-essential"):
                priority = "Essential"
            payment_mode = request.form.get("payment_mode", "UPI")
            if payment_mode not in PAYMENT_MODES:
                payment_mode = "Other"

            expenses.insert_one({
                "user_id": user_id(),
                "title": title,
                "category": category,
                "amount": money(request.form.get("amount")),
                "date": valid_date(request.form.get("date")),
                "payment_mode": payment_mode,
                "priority": priority,
                "note": request.form.get("note", "").strip()[:500],
                "created_at": datetime.now(timezone.utc)
            })
            flash("Expense saved.", "success")
            return redirect(url_for("transactions", kind="expense"))
        except (ValueError, PyMongoError) as exc:
            flash(str(exc) if isinstance(exc, ValueError) else "Could not save this expense. Check MongoDB.", "error")
    return render_template("add_expense.html")


@app.route("/add-income", methods=["GET", "POST"])
@login_required
def add_income():
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()[:120]
            if not title:
                raise ValueError("Please enter an income title.")
            income.insert_one({
                "user_id": user_id(),
                "title": title,
                "source": request.form.get("source", "Other").strip()[:80] or "Other",
                "amount": money(request.form.get("amount")),
                "date": valid_date(request.form.get("date")),
                "note": request.form.get("note", "").strip()[:500],
                "created_at": datetime.now(timezone.utc)
            })
            flash("Income saved.", "success")
            return redirect(url_for("transactions", kind="income"))
        except (ValueError, PyMongoError) as exc:
            flash(str(exc) if isinstance(exc, ValueError) else "Could not save this income. Check MongoDB.", "error")
    return render_template("add_income.html")


@app.route("/transactions")
@login_required
def transactions():
    uid = user_id()
    kind = request.args.get("kind", "all")
    query = expense_filters(request.args)
    exp_rows = [] if kind == "income" else list(expenses.find(query).sort([("date", -1), ("created_at", -1)]).limit(500))

    inc_query = {"user_id": uid}
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    search = request.args.get("q", "").strip()
    dr = {}
    if start:
        try:
            dr["$gte"] = valid_date(start)
        except ValueError:
            pass
    if end:
        try:
            dr["$lte"] = valid_date(end)
        except ValueError:
            pass
    if dr:
        inc_query["date"] = dr
    if search:
        safe_pattern = re.compile(re.escape(search[:80]), re.IGNORECASE)
        inc_query["$or"] = [{"title": safe_pattern}, {"source": safe_pattern}]
    inc_rows = [] if kind == "expense" else list(income.find(inc_query).sort([("date", -1), ("created_at", -1)]).limit(500))

    return render_template("transactions.html",
                           expenses=exp_rows,
                           income=inc_rows,
                           filters=request.args,
                           kind=kind,
                           filtered_expense_total=round(sum(float(x.get("amount", 0) or 0) for x in exp_rows), 2))


@app.route("/delete-expense/<id>", methods=["POST"])
@login_required
def delete_expense(id):
    if ObjectId.is_valid(id):
        expenses.delete_one(owner_filter({"_id": ObjectId(id)}))
        flash("Expense deleted.", "success")
    else:
        flash("Invalid expense identifier.", "error")
    return redirect(request.referrer or url_for("transactions"))


@app.route("/delete-income/<id>", methods=["POST"])
@login_required
def delete_income(id):
    if ObjectId.is_valid(id):
        income.delete_one(owner_filter({"_id": ObjectId(id)}))
        flash("Income deleted.", "success")
    else:
        flash("Invalid income identifier.", "error")
    return redirect(request.referrer or url_for("transactions"))


@app.route("/analytics")
@login_required
def analytics():
    uid = user_id()
    query = expense_filters(request.args)
    matched = list(expenses.find(query).sort("date", 1).limit(10000))
    category, monthly, priority_totals, payment_totals = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
    for row in matched:
        category[row.get("category", "Other")] += float(row.get("amount", 0) or 0)
        d = str(row.get("date") or "")[:7]
        if d:
            monthly[d] += float(row.get("amount", 0) or 0)
        priority_totals[row.get("priority", "Essential")] += float(row.get("amount", 0) or 0)
        payment_totals[row.get("payment_mode", "Other")] += float(row.get("amount", 0) or 0)

    categories = sorted(category.items(), key=lambda x: x[1], reverse=True)
    months = sorted(monthly.items())[-12:]
    total = round(sum(float(x.get("amount", 0) or 0) for x in matched), 2)
    filtered_income = aggregate_totals(income, {"user_id": uid})

    return render_template("analytics.html",
                           filters=request.args,
                           matched_count=len(matched),
                           expense_total=total,
                           income_total=filtered_income,
                           balance=round(filtered_income - total, 2),
                           category_labels=[x[0] for x in categories],
                           category_values=[round(x[1], 2) for x in categories],
                           month_labels=[x[0] for x in months],
                           month_values=[round(x[1], 2) for x in months],
                           priority_labels=list(priority_totals.keys()),
                           priority_values=[round(x, 2) for x in priority_totals.values()],
                           payment_labels=list(payment_totals.keys()),
                           payment_values=[round(x, 2) for x in payment_totals.values()],
                           category_rows=categories,
                           essential_total=round(priority_totals.get("Essential", 0), 2),
                           discretionary_total=round(priority_totals.get("Non-essential", 0), 2))


@app.route("/export.csv")
@login_required
def export_csv():
    query = expense_filters(request.args)
    rows = expenses.find(query).sort("date", -1)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Title", "Category", "Priority", "Payment mode", "Amount", "Note"])
    for row in rows:
        writer.writerow([
            row.get("date", ""),
            row.get("title", ""),
            row.get("category", ""),
            row.get("priority", ""),
            row.get("payment_mode", ""),
            row.get("amount", 0),
            row.get("note", "")
        ])
    return Response("\ufeff" + buffer.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=fintrack-expenses.csv"})


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():
    uid = user_id()
    if request.method == "POST":
        try:
            month = request.form.get("month", "")
            try:
                month = datetime.strptime(month, "%Y-%m").strftime("%Y-%m")
            except ValueError:
                raise ValueError("Choose a valid budget month.")
            category = request.form.get("category", "Overall").strip()
            if category not in (["Overall"] + CATEGORIES):
                category = "Overall"
            budgets.update_one(
                {"user_id": uid, "month": month, "category": category},
                {
                    "$set": {
                        "amount": money(request.form.get("amount")),
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            flash("Budget saved.", "success")
            return redirect(url_for("budget", month=month))
        except (ValueError, PyMongoError) as exc:
            flash(str(exc), "error")

    month = request.args.get("month", date.today().strftime("%Y-%m"))
    budget_rows = list(budgets.find({"user_id": uid, "month": month}).sort("category", 1))
    month_regex = re.compile(r"^" + re.escape(month))
    spend_rows = list(expenses.find({"user_id": uid, "date": month_regex}))
    spent = defaultdict(float)
    for row in spend_rows:
        spent[row.get("category", "Other")] += float(row.get("amount", 0) or 0)
    entries = []
    for b in budget_rows:
        actual = sum(spent.values()) if b.get("category") == "Overall" else spent.get(b.get("category", "Other"), 0)
        target = float(b.get("amount", 0) or 0)
        entries.append({
            **b,
            "spent": round(actual, 2),
            "percent": min(100, round(actual / target * 100)) if target > 0 else 0
        })
    return render_template("budget.html", budgets=entries, selected_month=month)


@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings_page():
    uid = user_id()
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()[:120]
            if not title:
                raise ValueError("Enter a savings entry name.")
            savings.insert_one({
                "user_id": uid,
                "title": title,
                "amount": money(request.form.get("amount")),
                "date": valid_date(request.form.get("date")),
                "note": request.form.get("note", "").strip()[:500],
                "created_at": datetime.now(timezone.utc)
            })
            flash("Savings entry recorded.", "success")
            return redirect(url_for("savings_page"))
        except (ValueError, PyMongoError) as exc:
            flash(str(exc), "error")
    rows = list(savings.find({"user_id": uid}).sort("date", -1))
    return render_template("savings.html", savings=rows, savings_total=round(sum(float(r.get("amount", 0) or 0) for r in rows), 2))


@app.route("/bills", methods=["GET", "POST"])
@login_required
def bills_page():
    uid = user_id()
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()[:120]
            if not title:
                raise ValueError("Enter a bill name.")
            status = request.form.get("status", "Upcoming")
            if status not in ("Upcoming", "Paid"):
                status = "Upcoming"
            bills.insert_one({
                "user_id": uid,
                "title": title,
                "amount": money(request.form.get("amount")),
                "due_date": valid_date(request.form.get("due_date"), "Due date"),
                "status": status,
                "created_at": datetime.now(timezone.utc)
            })
            flash("Bill saved.", "success")
            return redirect(url_for("bills_page"))
        except (ValueError, PyMongoError) as exc:
            flash(str(exc), "error")
    rows = list(bills.find({"user_id": uid}).sort("due_date", 1))
    return render_template("bills.html", bills=rows)


@app.route("/bills/<id>/toggle", methods=["POST"])
@login_required
def toggle_bill(id):
    if ObjectId.is_valid(id):
        row = bills.find_one(owner_filter({"_id": ObjectId(id)}))
        if row:
            bills.update_one({"_id": row["_id"]}, {"$set": {"status": "Paid" if row.get("status") != "Paid" else "Upcoming"}})
    return redirect(request.referrer or url_for("bills_page"))


@app.route("/goals", methods=["GET", "POST"])
@login_required
def goals_page():
    uid = user_id()
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()[:120]
            if not title:
                raise ValueError("Enter a goal name.")
            target = money(request.form.get("target_amount"), "Target amount")
            saved = money_non_negative(request.form.get("saved_amount", 0), "Saved amount")
            goals.insert_one({
                "user_id": uid,
                "title": title,
                "target_amount": target,
                "saved_amount": saved,
                "deadline": valid_date(request.form.get("deadline"), "Deadline"),
                "created_at": datetime.now(timezone.utc)
            })
            flash("Financial goal created.", "success")
            return redirect(url_for("goals_page"))
        except (ValueError, PyMongoError) as exc:
            flash(str(exc), "error")
    rows = list(goals.find({"user_id": uid}).sort("deadline", 1))
    for row in rows:
        target_val = float(row.get("target_amount", 0) or 0)
        saved_val = float(row.get("saved_amount", 0) or 0)
        row["percent"] = min(100, round(saved_val / target_val * 100)) if target_val > 0 else 0
    return render_template("goals.html", goals=rows)


@app.errorhandler(PyMongoError)
def database_error(_error):
    flash("MongoDB connection failed. Start MongoDB Server and verify your MONGO_URI.", "error")
    return render_template("error.html", title="Database unavailable"), 503


@app.errorhandler(404)
def page_not_found(_error):
    return render_template("error.html", title="Page not found"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "0") == "1")
