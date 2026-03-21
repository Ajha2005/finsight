import pandas as pd
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from datetime import datetime


REQUIRED_COLUMNS = {"date", "description", "amount"}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip all column names so we handle any bank's format."""
    df.columns = [col.strip().lower() for col in df.columns]
    return df


def validate_columns(df: pd.DataFrame):
    """Make sure the CSV has the columns we need."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates, clean amounts, drop bad rows."""

    # Drop completely empty rows
    df = df.dropna(how="all")

    # Parse date column — handles most common formats
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

    # Drop rows where date couldn't be parsed
    invalid_dates = df["date"].isna().sum()
    if invalid_dates > 0:
        print(f"⚠️  Dropping {invalid_dates} rows with unparseable dates")
    df = df.dropna(subset=["date"])

    # Clean amount — remove currency symbols, commas
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(r"[₹$,\s]", "", regex=True)
        .astype(float)
    )

    # Convert date to Python date object
    df["date"] = df["date"].dt.date

    # Clean description
    df["description"] = df["description"].astype(str).str.strip()

    return df


def ingest_csv(file, db: Session) -> dict:
    """
    Main ingestion function.
    Takes an uploaded file + DB session.
    Returns a summary of what was ingested.
    """

    # Read CSV
    try:
        df = pd.read_csv(file)
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}")

    # Normalize and validate
    df = normalize_columns(df)
    validate_columns(df)

    # Clean
    df = clean_dataframe(df)

    if df.empty:
        raise ValueError("No valid transactions found in the CSV.")

    # Save to database
    saved = 0
    skipped = 0

    for _, row in df.iterrows():
        # Skip duplicate: same date + description + amount
        exists = db.query(Transaction).filter(
            Transaction.date == row["date"],
            Transaction.description == row["description"],
            Transaction.amount == row["amount"]
        ).first()

        if exists:
            skipped += 1
            continue

        transaction = Transaction(
            date=row["date"],
            description=row["description"],
            amount=row["amount"],
        )
        db.add(transaction)
        saved += 1

    db.commit()

    return {
        "total_rows": len(df),
        "saved": saved,
        "skipped_duplicates": skipped
    }