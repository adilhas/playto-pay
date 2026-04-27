# Playto Payout Engine (Django + DRF + Celery)

Minimal payout engine for merchants receiving credits and requesting INR withdrawals.

## Overview

This service implements a ledger-driven payout flow with:

- **Integer money model** in paise (`BigIntegerField`), no floats.
- **Derived balance** from ledger entries (`SUM(amount_paise)`).
- **Concurrency-safe payout creation** using DB transaction + row lock.
- **Idempotent payout API** with `Idempotency-Key` and unique DB constraint.
- **Async payout processing** via Celery.
- **Retry handling** for stuck payouts (up to 3 attempts, then fail + refund).

### High-level flow

1. Merchant has ledger credits.
2. Merchant sends payout request (`POST /api/v1/payouts/`) with idempotency key.
3. API validates + locks merchant row + creates pending payout + writes debit hold.
4. Celery worker processes payout (`pending -> processing -> completed|failed`).
5. On failure, held funds are returned via ledger credit.

---

## Tech stack

- Python 3.13
- Django + Django REST Framework
- PostgreSQL (via `DATABASE_URL`)
- Celery + Redis
- django-celery-beat
- JWT auth (`rest_framework_simplejwt`)

---

## How to run

## 1) Prerequisites

- Python 3.13
- PostgreSQL running
- Redis running
- Pipenv installed

## 2) Environment variables

Create `.env` in project root:

```env
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<db_name>
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
```

> `DATABASE_URL` is required by `config/settings.py`.

## 3) Install dependencies

```bash
pipenv install
```

## 4) Run migrations

```bash
pipenv run python manage.py migrate
```

## 5) Create a user (merchant auto-created)

```bash
pipenv run python manage.py createsuperuser
```

A `Merchant` is auto-created via `post_save` signal on `User`.

## 6) Seed sample data

```bash
pipenv run python seed.py
```

This seeds 3 users (`user1`, `user2`, `user3`) with initial credit entries.

## 7) Start API server

```bash
pipenv run python manage.py runserver
```

## 8) Start Celery worker

```bash
pipenv run celery -A config worker -l info
```

## 9) Start Celery beat (for periodic retries)

```bash
pipenv run celery -A config beat -l info
```

> `retry_stuck_payouts` exists in code. If you want periodic execution, configure it in django-celery-beat/admin.

---

## Authentication

All API routes use JWT Bearer auth.

### Login

**POST** `/api/v1/auth/login/`

#### Request

```json
{
  "username": "user1",
  "password": "your_password"
}
```

#### Response (200)

```json
{
  "refresh": "<jwt-refresh-token>",
  "access": "<jwt-access-token>"
}
```

Use access token in headers:

```http
Authorization: Bearer <access_token>
```

---

## API endpoints + request/response demos

## 1) Get current merchant info

**GET** `/api/v1/accounts/me/`

#### Response (200)

```json
{
  "user": "user1",
  "merchant_id": 1
}
```

---

## 2) Create bank account

**POST** `/api/v1/accounts/bank-accounts/`

#### Request

```json
{
  "account_number": "1234567890",
  "ifsc_code": "HDFC0001234"
}
```

#### Response (201)

```json
{
  "id": 1,
  "account_number": "1234567890",
  "ifsc_code": "HDFC0001234"
}
```

---

## 3) Get balance

**GET** `/api/v1/ledger/balance/`

#### Response (200)

```json
{
  "balance_paise": 100000
}
```

---

## 4) Create payout request

**POST** `/api/v1/payouts/`

Required header:

```http
Idempotency-Key: <merchant-scoped-unique-key>
```

#### Request

```json
{
  "amount_paise": 25000,
  "bank_account_id": 1
}
```

#### Success response (200)

```json
{
  "payout_id": 10,
  "status": "pending"
}
```

#### Common error responses

- Missing idempotency key:

```json
{
  "error": "Idempotency-Key header required"
}
```

- Invalid amount:

```json
{
  "error": "Invalid amount"
}
```

- Insufficient balance:

```json
{
  "error": "Insufficient balance"
}
```

- Invalid bank account:

```json
{
  "error": "Invalid bank account"
}
```

#### Idempotency behavior

If same merchant sends same `Idempotency-Key` again, response is reused:

```json
{
  "payout_id": 10,
  "status": "pending"
}
```

---

## Quick cURL demo

```bash
# 1) login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"user1","password":"pass"}' | jq -r .access)

# 2) create bank account
curl -s -X POST http://127.0.0.1:8000/api/v1/accounts/bank-accounts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"account_number":"1234567890","ifsc_code":"HDFC0001234"}'

# 3) check balance
curl -s http://127.0.0.1:8000/api/v1/ledger/balance/ \
  -H "Authorization: Bearer $TOKEN"

# 4) create payout (with idempotency key)
curl -s -X POST http://127.0.0.1:8000/api/v1/payouts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Idempotency-Key: 11111111-1111-1111-1111-111111111111" \
  -H 'Content-Type: application/json' \
  -d '{"amount_paise":25000,"bank_account_id":1}'
```

---

## Notes / known gaps

- Idempotency-key TTL (24 hours) is not implemented yet.
- Retry path exists, but explicit exponential backoff scheduling is not implemented.
- There is currently no dedicated payout history/list endpoint in this API.

---

## Testing

Project includes tests for:

- Concurrency payout behavior.
- Idempotency behavior.

Run:

```bash
pipenv run python manage.py test
```
