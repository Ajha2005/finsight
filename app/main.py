from fastapi import FastAPI
from app.database import Base, engine
from app.api import routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinSight API",
    description="Personal Finance Anomaly Detection & Intelligence API",
    version="1.0.0"
)

app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to FinSight API", "docs": "/docs"}