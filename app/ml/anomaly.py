import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
from sqlalchemy.orm import Session
from app.models.transaction import Transaction


# ─── Feature Engineering ──────────────────────────────────────────────────────

def build_features(transactions: list) -> pd.DataFrame:
    """
    Convert transaction objects into a numeric feature matrix.
    ML models only understand numbers — so we engineer features from raw data.
    """
    records = []

    for t in transactions:
        records.append({
            "amount": abs(t.amount),               # absolute value of amount
            "is_debit": 1 if t.amount < 0 else 0,  # debit or credit
            "day_of_week": t.date.weekday(),        # 0=Monday, 6=Sunday
            "day_of_month": t.date.day,             # 1-31
            "category": t.category or "miscellaneous"
        })

    df = pd.DataFrame(records)

    # Encode category as a number
    le = LabelEncoder()
    df["category_encoded"] = le.fit_transform(df["category"])
    df = df.drop(columns=["category"])

    return df


# ─── Isolation Forest ─────────────────────────────────────────────────────────

def detect_anomalies(db: Session) -> dict:
    """
    Main anomaly detection function.
    Loads all transactions, fits Isolation Forest, updates DB with results.
    """

    # Load all transactions that have been categorized
    transactions = db.query(Transaction).all()

    if len(transactions) < 5:
        return {
            "status": "skipped",
            "reason": "Need at least 5 transactions to detect anomalies",
            "total": len(transactions)
        }

    # Build feature matrix
    features = build_features(transactions)

    # ── Fit Isolation Forest ──
    # contamination = expected proportion of anomalies in data
    # 0.05 means we expect ~5% of transactions to be anomalous
    model = IsolationForest(
        n_estimators=100,       # number of trees
        contamination=0.05,     # expected anomaly rate
        random_state=42         # for reproducibility
    )

    model.fit(features)

    # Predict: -1 = anomaly, 1 = normal
    predictions = model.predict(features)

    # Anomaly scores: more negative = more anomalous
    scores = model.decision_function(features)

    # ── Update database ──
    flagged = 0

    for i, transaction in enumerate(transactions):
        transaction.is_anomaly = 1 if predictions[i] == -1 else 0
        transaction.anomaly_score = round(float(scores[i]), 4)
        if predictions[i] == -1:
            flagged += 1

    db.commit()

    return {
        "status": "completed",
        "total_transactions": len(transactions),
        "anomalies_found": flagged,
        "anomaly_rate": f"{round(flagged / len(transactions) * 100, 1)}%"
    }