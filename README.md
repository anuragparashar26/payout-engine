# Payout Engine

A minimal payout engine - helping Indian agencies and freelancers collect and withdraw international payments.


## Tech Stack

- **Backend**: Django 4.2, Django REST Framework, Celery
- **Frontend**: React 18, Vite, Tailwind CSS
- **Database**: PostgreSQL 15
- **Queue**: Redis 7

---

## Features

- Merchant balance tracking in paise
- Idempotent payout requests 
- Concurrent request handling via database-level locking
- State machine: pending → processing → completed/failed
- Retry logic with exponential backoff (30s timeout, max 3 attempts)
- Seed data with 3 merchants and credit history

---

## Docker Installation

### 1. Configure

```bash
cp .env.example .env
# Edit .env as needed
```

### 2. Start

```bash
docker compose up --build
```

Services:
| Service | Port |
|---------|------|
| Frontend | 5173 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

Access at http://localhost:5173

---

## Local Installation

### 1. Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment

Create `.env` file in backend directory:

```env
SECRET_KEY=your-secret-key
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=payout_engine
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### 4. Database

```bash
python manage.py migrate
python manage.py seed_data
```

### 5. Run Services

**Terminal 1 - Backend:**
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
celery -A config worker --loglevel=info
```

**Terminal 3 - Frontend:**
```bash
cd ../frontend
npm install
npm run dev
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/balance/` | GET | Get merchant balance |
| `/api/v1/payouts/` | GET | List payouts |
| `/api/v1/payouts/` | POST | Create payout |
| `/api/v1/payouts/<id>/` | GET | Get payout details |
| `/api/v1/ledger/` | GET | List ledger entries |
| `/api/v1/bank-accounts/` | GET | List bank accounts |
| `/api/v1/credits/` | POST | Add credits |

### Create Payout

```bash
curl -X POST http://localhost:8000/api/v1/payouts/ \
  -H "Authorization: ravi-token-dev" \
  -H "Idempotency-Key: <uuid>" \
  -H "Content-Type: application/json" \
  -d '{"amount_paise": 500000, "bank_account_id": "<uuid>"}'
```

---

## Running Tests

```bash
cd backend
pytest
```