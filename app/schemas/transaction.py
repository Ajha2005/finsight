from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class TransactionBase(BaseModel):
    date: date
    description: str
    amount: float

class TransactionOut(TransactionBase):
    id: int
    category: Optional[str]
    is_anomaly: int
    anomaly_score: Optional[float]
    uploaded_at: datetime

    class Config:
        from_attributes = True