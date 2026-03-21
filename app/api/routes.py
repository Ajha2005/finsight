from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.ingestion import ingest_csv
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionOut
from app.core.config import settings

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


# ─── Get All Transactions ─────────────────────────────────────────────────────

@router.get("/transactions", response_model=List[TransactionOut], dependencies=[Depends(verify_api_key)])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Returns all stored transactions.
    Use skip and limit for pagination.
    """
    transactions = db.query(Transaction).offset(skip).limit(limit).all()
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