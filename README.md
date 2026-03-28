# FinSight API

> A production-style personal finance intelligence API that ingests bank statements,
> detects spending anomalies using Machine Learning, and delivers automated weekly reports.

![CI](https://github.com/Ajha2005/finsight/actions/workflows/ci.yml/badge.svg)

---

## What it does

Most people have no idea where their money goes. FinSight solves this by:

- Ingesting raw bank statement CSVs and cleaning messy real-world data
- Auto-categorizing every transaction (food, transport, groceries, etc.) using TF-IDF + keyword ML
- Detecting unusual spending with **Isolation Forest** — an unsupervised ML algorithm
- Exposing everything through a clean, versioned, authenticated REST API
- Running **automated weekly reports** and **anomaly alerts** via email on a schedule
- Full **CI/CD pipeline** that runs tests on every push

---

## Architecture
```
CSV Upload → Parsing & Cleaning → ML Categorization → Anomaly Detection → PostgreSQL
                                                                               ↓
                                                                    REST API (FastAPI)
                                                                               ↓
                                                           APScheduler (background jobs)
                                                                               ↓
                                                                    Email Alerts & Reports
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI (Python) |
| Database | PostgreSQL + SQLAlchemy |
| ML | scikit-learn (TF-IDF, Isolation Forest) |
| Scheduler | APScheduler |
| Containers | Docker |
| CI/CD | GitHub Actions |
| Testing | pytest |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/transactions/upload` | Upload bank statement CSV |
| GET | `/api/v1/transactions` | List transactions (with filters) |
| GET | `/api/v1/transactions/{id}` | Get single transaction |
| GET | `/api/v1/transactions/anomalies/all` | Get flagged anomalies |
| GET | `/api/v1/insights` | Full financial summary |
| GET | `/api/v1/report/weekly` | Weekly financial report |
| DELETE | `/api/v1/transactions/all` | Delete all transactions |

> All endpoints except `/health` require header: `x-api-key`

---

## Filters on `/transactions`

| Parameter | Type | Example |
|---|---|---|
| `category` | string | `food`, `groceries`, `transport` |
| `is_anomaly` | int | `1` = anomalies only |
| `date_from` | date | `2024-01-01` |
| `date_to` | date | `2024-01-31` |
| `min_amount` | float | `-500` |
| `max_amount` | float | `0` |

---

## ML Details

### Transaction Categorizer
- **Layer 1**: Keyword matching against curated category lists (fast, handles 80% of cases)
- **Layer 2**: TF-IDF cosine similarity fallback for unrecognized merchants
- Categories: food, groceries, transport, shopping, utilities, entertainment, health, income, and more

### Anomaly Detector
- Algorithm: **Isolation Forest** (unsupervised)
- Features: transaction amount, debit/credit flag, day of week, day of month, category
- Contamination rate: 5% (flags ~1 in 20 transactions as anomalous)
- Runs automatically after every CSV upload

---

## Automated Jobs

| Job | Schedule | What it does |
|---|---|---|
| Weekly Report | Every Monday 8:00 AM | Generates report and emails it |
| Anomaly Check | Every day 9:00 AM | Checks for anomalies and sends alert |

---

## Project Structure
```
finsight/
├── app/
│   ├── api/
│   │   └── routes.py          # All API endpoints
│   ├── core/
│   │   └── config.py          # Settings from .env
│   ├── ml/
│   │   ├── categorizer.py     # TF-IDF transaction categorizer
│   │   └── anomaly.py         # Isolation Forest anomaly detector
│   ├── models/
│   │   └── transaction.py     # Database model
│   ├── schemas/
│   │   └── transaction.py     # API request/response schemas
│   ├── services/
│   │   ├── ingestion.py       # CSV parsing and storage
│   │   ├── report.py          # Weekly report generation
│   │   ├── scheduler.py       # APScheduler background jobs
│   │   └── email.py           # Email alerts
│   ├── main.py                # FastAPI app entry point
│   └── database.py            # DB connection and session
├── tests/
│   └── test_ingestion.py      # pytest test suite
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI/CD
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
