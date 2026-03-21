# FinSight API

A personal finance intelligence API that ingests bank statement CSVs,
detects spending anomalies using Machine Learning, and exposes everything
through a clean versioned REST API.

## Features

- CSV ingestion with automatic cleaning and deduplication
- ML-based transaction categorization (Day 2)
- Anomaly detection using Isolation Forest (Day 2)
- Scheduled weekly financial pulse reports (Day 4)
- API key authentication
- Fully containerized with Docker
- CI/CD via GitHub Actions

## Tech Stack

- **API**: FastAPI (Python)
- **Database**: PostgreSQL + SQLAlchemy
- **ML**: scikit-learn
- **Containers**: Docker + docker-compose
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites
- Python 3.11+
- Docker Desktop

### Setup

1. Clone the repo
```bash
   git clone https://github.com/yourusername/finsight.git
   cd finsight
```

2. Create virtual environment
```bash
   python -m venv venv
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
```

3. Create `.env` file
```env
   DATABASE_URL=postgresql://finsight_user:finsight_pass@localhost:5432/finsight_db
   POSTGRES_USER=finsight_user
   POSTGRES_PASSWORD=finsight_pass
   POSTGRES_DB=finsight_db
   API_KEY=mysecretapikey123
```

4. Start the database
```bash
   docker-compose up -d
```

5. Start the API
```bash
   uvicorn app.main:app --reload
```

6. Visit `http://localhost:8000/docs` for interactive API docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/transactions/upload` | Upload CSV |
| GET | `/api/v1/transactions` | List transactions |
| GET | `/api/v1/transactions/{id}` | Get one transaction |
| GET | `/api/v1/transactions/anomalies/all` | Get anomalies |
| DELETE | `/api/v1/transactions/all` | Delete all |

> All endpoints except `/health` require header: `x-api-key`

## CSV Format
```csv
Date,Description,Amount
2024-01-05,AMAZON PURCHASE,-45.99
2024-01-06,SALARY CREDIT,50000.00
```