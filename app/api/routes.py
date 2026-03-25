from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.services.ingestion import ingest_csv
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionOut
from app.core.config import settings
from app.services.report import generate_weekly_report
from sqlalchemy import func

router = APIRouter()


# ─── Auth helper ────────────────────────────────────────────────────────────

def verify_api_key(x_api_key: str = Header(...)):
    """Every endpoint requires this header: x-api-key: mysecretapikey123"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ─── Health Check ────────────────────────────────────────────────────────────

@router.get("/health")
def health_check():
    return {"status": "ok"}


# ─── Upload CSV ──────────────────────────────────────────────────────────────

@router.post("/transactions/upload", dependencies=[Depends(verify_api_key)])
async def upload_transactions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a bank statement CSV.
    Required header: x-api-key
    Required columns in CSV: date, description, amount
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    try:
        result = ingest_csv(file.file, db)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "message": "Upload successful",
        "filename": file.filename,
        "summary": result
    }


# ─── Get All Transactions (with filters) ─────────────────────────────────────────────────────
# ─── Get All Transactions (with filters) ─────────────────────────────────────

@router.get("/transactions", response_model=List[TransactionOut], dependencies=[Depends(verify_api_key)])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    is_anomaly: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Returns transactions with optional filters.

    - **category**: filter by category (e.g. food, groceries, transport)
    - **is_anomaly**: 1 for anomalies only, 0 for normal only
    - **date_from** / **date_to**: filter by date range (YYYY-MM-DD)
    - **min_amount** / **max_amount**: filter by amount range
    - **skip** / **limit**: pagination
    """
    query = db.query(Transaction)

    if category:
        query = query.filter(Transaction.category == category.lower())

    if is_anomaly is not None:
        query = query.filter(Transaction.is_anomaly == is_anomaly)

    if date_from:
        query = query.filter(Transaction.date >= date_from)

    if date_to:
        query = query.filter(Transaction.date <= date_to)

    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
    return transactions



# ─── Get Single Transaction ───────────────────────────────────────────────────

@router.get("/transactions/{transaction_id}", response_model=TransactionOut, dependencies=[Depends(verify_api_key)])
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Returns a single transaction by ID."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


# ─── Get Anomalies ────────────────────────────────────────────────────────────

@router.get("/transactions/anomalies/all", response_model=List[TransactionOut], dependencies=[Depends(verify_api_key)])
def get_anomalies(db: Session = Depends(get_db)):
    """Returns all transactions flagged as anomalies."""
    anomalies = db.query(Transaction).filter(Transaction.is_anomaly == 1).all()
    return anomalies


# ─── Delete All Transactions ──────────────────────────────────────────────────

@router.delete("/transactions/all", dependencies=[Depends(verify_api_key)])
def delete_all_transactions(db: Session = Depends(get_db)):
    """Wipes all transactions. Useful during development."""
    count = db.query(Transaction).delete()
    db.commit()
    return {"message": f"Deleted {count} transactions"}

# ─── Insights / Summary ───────────────────────────────────────────────────────

@router.get("/insights", dependencies=[Depends(verify_api_key)])
def get_insights(db: Session = Depends(get_db)):
    """
    Returns a full financial summary:
    - Total spent and total income
    - Spending by category
    - Anomaly count and rate
    - Biggest single transaction
    - Most frequent merchant
    """

    transactions = db.query(Transaction).all()

    if not transactions:
        return {"message": "No transactions found. Upload a CSV first."}

    # ── Basic totals ──
    total_spent = sum(abs(t.amount) for t in transactions if t.amount < 0)
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    net = total_income - total_spent

    # ── Spending by category ──
    category_totals = {}
    for t in transactions:
        if t.amount < 0:  # only debits
            cat = t.category or "miscellaneous"
            category_totals[cat] = category_totals.get(cat, 0) + abs(t.amount)

    # Sort categories by amount descending
    top_categories = sorted(
        [{"category": k, "total_spent": round(v, 2)} for k, v in category_totals.items()],
        key=lambda x: x["total_spent"],
        reverse=True
    )

    # ── Anomalies ──
    anomaly_count = sum(1 for t in transactions if t.is_anomaly == 1)
    anomaly_rate = round(anomaly_count / len(transactions) * 100, 1)

    # ── Biggest transaction ──
    biggest = max(transactions, key=lambda t: abs(t.amount))

    # ── Most frequent description ──
    description_counts = {}
    for t in transactions:
        desc = t.description.upper()
        description_counts[desc] = description_counts.get(desc, 0) + 1
    most_frequent = max(description_counts, key=description_counts.get)

    # ── Date range ──
    dates = [t.date for t in transactions]
    date_from = min(dates)
    date_to = max(dates)

    return {
        "summary": {
            "total_transactions": len(transactions),
            "date_range": {
                "from": str(date_from),
                "to": str(date_to)
            },
            "total_spent": round(total_spent, 2),
            "total_income": round(total_income, 2),
            "net": round(net, 2)
        },
        "top_categories": top_categories,
        "anomalies": {
            "count": anomaly_count,
            "rate_percent": anomaly_rate
        },
        "biggest_transaction": {
            "date": str(biggest.date),
            "description": biggest.description,
            "amount": biggest.amount,
            "category": biggest.category,
            "is_anomaly": biggest.is_anomaly
        },
        "most_frequent_merchant": {
            "description": most_frequent,
            "occurrences": description_counts[most_frequent]
        }
    }
# ─── Weekly Report ────────────────────────────────────────────────────────────

@router.get("/report/weekly", dependencies=[Depends(verify_api_key)])
def weekly_report(
    weeks_ago: int = 0,
    db: Session = Depends(get_db)
):
   
    return generate_weekly_report(db, weeks_ago=weeks_ago)

