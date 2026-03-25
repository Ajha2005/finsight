from fastapi import FastAPI
from app.database import Base, engine
from app.api import routes
from app.services.scheduler import start_scheduler
from contextlib import asynccontextmanager


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on startup
    scheduler = start_scheduler()
    yield
    # Runs on shutdown
    scheduler.shutdown()


app = FastAPI(
    title="FinSight API",
    description="Personal Finance Anomaly Detection & Intelligence API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Welcome to FinSight API", "docs": "/docs"}