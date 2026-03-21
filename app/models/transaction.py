from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)       # assigned by ML
    is_anomaly = Column(Integer, default=0)        # 0 = normal, 1 = anomaly
    anomaly_score = Column(Float, nullable=True)   # how anomalous (lower = more anomalous)
    uploaded_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Transaction {self.date} | {self.description} | {self.amount}>"