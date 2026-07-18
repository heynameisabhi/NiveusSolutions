# Veritas Claims Analytics

A production-style prototype of a **configurable medical data standardization pipeline** that ingests heterogeneous JSON medical reports, standardizes them, validates results, stores them in a relational database, and exposes an operational React dashboard.

---

## Architecture

```
JSON Files
    │
    ▼
┌─────────────┐
│  Ingestion  │  Scan folder, detect clinic, compute hash
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Parser    │  Apply per-clinic YAML field mappings (dot-notation)
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Standardizer    │  RapidFuzz fuzzy match, unit conversion,
│                  │  gender/age normalization, medicine mapping
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│  Validator  │  Reference range checks, outlier detection,
│             │  5-class classification
└──────┬──────┘
       │
       ▼
┌───────────────┐
│ Deduplicator  │  Content hash + semantic key dedup
└──────┬────────┘
       │
       ▼
┌────────────┐
│   Loader   │  Idempotent DB insert, full audit trail
└──────┬─────┘
       │
       ▼
 PostgreSQL / SQLite
       │
       ▼
 FastAPI REST API
       │
       ▼
 React Dashboard
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | FastAPI (Python) |
| Processing | Python modules |
| Database | SQLite (default) / PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic v2 |
| Fuzzy Matching | RapidFuzz |
| Testing | Pytest (49 tests) |
| Charts | Recharts |
| Config | YAML + JSON |

---

## Project Structure

```
medical-standardizer/
├── src/
│   ├── api/routes.py           # FastAPI routers
│   ├── ingestion/ingestion.py  # File scanner
│   ├── parser/parser.py        # Config-driven field mapper
│   ├── standardizer/           # Core normalization engine
│   ├── validator/validator.py  # Reference range checks
│   ├── deduplicator/           # Hash-based dedup
│   ├── loader/loader.py        # DB insert
│   ├── services/pipeline.py    # Orchestration
│   ├── database/engine.py      # SQLAlchemy setup
│   ├── models/models.py        # ORM models
│   ├── schemas/schemas.py      # Pydantic schemas
│   └── config_loader/loader.py # YAML/JSON config reader
├── config/
│   ├── clinics/clinic_a.yaml   # Per-clinic field mapping
│   ├── clinics/clinic_b.yaml
│   ├── reference_ranges.json
│   ├── unit_mapping.json
│   ├── medicine_mapping.json
│   └── test_mapping.json
├── sample-data/                # 4 heterogeneous JSON reports
├── frontend/                   # React dashboard
├── tests/                      # 49 unit + integration tests
├── main.py                     # FastAPI entry point
└── .env                        # Configuration
```

---

## Quick Start

### Backend

```bash
cd medical-standardizer

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload
# → http://localhost:8000
# → API docs: http://localhost:8000/docs
```

### Frontend

```bash
cd medical-standardizer/frontend

npm install
npm run dev
# → http://localhost:5173
```

### Run Pipeline

Click **Run Pipeline** in the sidebar, or call the API directly:

```bash
curl -X POST http://localhost:8000/api/ingest
```

### Run Tests

```bash
cd medical-standardizer
pytest tests/ -v
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard` | Overall stats + run history |
| GET | `/api/records` | Paginated standardized reports |
| GET | `/api/records/{id}` | Full record detail (raw + standardized) |
| GET | `/api/flags` | Flagged records (filterable) |
| GET | `/api/clinics` | Registered clinics |
| GET | `/api/clinics/analytics` | Per-clinic metrics |
| POST | `/api/ingest` | Trigger pipeline run |

---

## Configuration-Driven Design

Adding a **new clinic** requires only one file:

```yaml
# config/clinics/clinic_c.yaml
clinic_id: clinic_c
clinic_name: NewClinc Hospital

field_mappings:
  patient_id: patientData.ID
  patient_name: patientData.name
  gender: patientData.gender
  report_date: reportDate
  lab_results:
    hemoglobin: results.HGB
    glucose: results.GLU

dedup_fields:
  - patient_id
  - clinic_id
  - report_date
```

No code changes required. The pipeline auto-discovers the new config on next run.

---

## Database (Switch to PostgreSQL)

Edit `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/veritas_claims
```

Also uncomment `psycopg2-binary` in `requirements.txt` and run `pip install -r requirements.txt`.

---

## Design Decisions

**Why config-driven?** Adding a clinic is an ops task, not a dev task. Zero code deploys.

**Why RapidFuzz over AI?** Fast, deterministic, no API costs, easy to audit and override.

**Why SQLite by default?** Zero infrastructure for prototyping. Same SQLAlchemy ORM switches to PostgreSQL with one env var.

**How would this scale to 200k+ files/day?** Replace the synchronous pipeline with Celery workers + Redis queue. Add GCS/S3 blob storage for raw files. Use PostgreSQL with partitioned tables by clinic_id + month.

**How would you migrate to GCS + BigQuery?** Store raw JSON in GCS, write standardized output to BigQuery via streaming inserts. Keep PostgreSQL for operational metadata (runs, flags). Use Dataflow for batch processing.
