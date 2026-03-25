from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from datetime import date, timedelta


def generate_weekly_report(db: Session, weeks_ago: int = 0) -> dict:
    """
    Generates a weekly financial report.
    weeks_ago=0 means current week, weeks_ago=1 means last week, etc.
    """

    # ── Calculate week date range ──
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
    end_of_week = start_of_week + timedelta(days=6)

    # ── Fetch this week's transactions ──
    transactions = db.query(Transaction).filter(
        Transaction.date >= start_of_week,
        Transaction.date <= end_of_week
    ).all()

    # ── Fetch previous week for comparison ──
    prev_start = start_of_week - timedelta(weeks=1)
    prev_end = end_of_week - timedelta(weeks=1)
    prev_transactions = db.query(Transaction).filter(
        Transaction.date >= prev_start,
        Transaction.date <= prev_end
    ).all()

    # ── This week stats ──
    total_spent = sum(abs(t.amount) for t in transactions if t.amount < 0)
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    anomaly_count = sum(1 for t in transactions if t.is_anomaly == 1)

    # ── Previous week stats for comparison ──
    prev_spent = sum(abs(t.amount) for t in prev_transactions if t.amount < 0)

    # ── Spending change ──
    if prev_spent > 0:
        spending_change = round(((total_spent - prev_spent) / prev_spent) * 100, 1)
    else:
        spending_change = None

    # ── Category breakdown ──
    category_totals = {}
    for t in transactions:
        if t.amount < 0:
            cat = t.category or "miscellaneous"
            category_totals[cat] = category_totals.get(cat, 0) + abs(t.amount)

    top_categories = sorted(
        [{"category": k, "total_spent": round(v, 2)} for k, v in category_totals.items()],
        key=lambda x: x["total_spent"],
        reverse=True
    )[:5]  # top 5 only

    # ── Anomalies detail ──
    anomalies = [
        {
            "date": str(t.date),
            "description": t.description,
            "amount": t.amount,
            "category": t.category,
            "anomaly_score": t.anomaly_score
        }
        for t in transactions if t.is_anomaly == 1
    ]

    # ── Biggest expense ──
    expenses = [t for t in transactions if t.amount < 0]
    biggest_expense = None
    if expenses:
        biggest = min(expenses, key=lambda t: t.amount)
        biggest_expense = {
            "date": str(biggest.date),
            "description": biggest.description,
            "amount": biggest.amount,
            "category": biggest.category
        }

    # ── Generate human readable verdict ──
    if spending_change is None:
        verdict = "No previous week data to compare."
    elif spending_change > 20:
        verdict = f"⚠️ Spending is up {spending_change}% compared to last week. Watch out!"
    elif spending_change < -10:
        verdict = f"✅ Great job! Spending is down {abs(spending_change)}% from last week."
    else:
        verdict = f"Spending is relatively stable ({spending_change:+.1f}% vs last week)."

    return {
        "report_period": {
            "from": str(start_of_week),
            "to": str(end_of_week)
        },
        "summary": {
            "total_transactions": len(transactions),
            "total_spent": round(total_spent, 2),
            "total_income": round(total_income, 2),
            "net": round(total_income - total_spent, 2),
            "anomalies_flagged": anomaly_count
        },
        "vs_last_week": {
            "last_week_spent": round(prev_spent, 2),
            "change_percent": spending_change,
            "verdict": verdict
        },
        "top_categories": top_categories,
        "anomalies": anomalies,
        "biggest_expense": biggest_expense
    }