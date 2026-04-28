# EXPLAINER.md

# Playto Founding Engineer Challenge – Explainer

This project is a minimal payout engine built with:

- Backend: Django + Django REST Framework
- Frontend: React + Tailwind CSS
- Database: PostgreSQL
- Background Worker: Celery + Redis
- Deployment: Render / Railway

The goal was to build a system where merchants can:

- View balances
- Request payouts
- Prevent overdraft
- Handle duplicate API retries
- Process payouts asynchronously
- Maintain correct ledger records

---

# 1. The Ledger

## Why ledger model?

Instead of storing one changing balance column, I used immutable ledger entries.

Each money movement creates one row.

Examples:

- `credit` = customer payment added
- `hold` = payout requested, reserve funds
- `debit` = payout completed
- `release` = payout failed, return funds

This gives:

- full audit trail
- safer accounting
- easier reconciliation
- no hidden balance corruption

---

## Ledger Model Example

python
class LedgerEntry(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    payout = models.ForeignKey(Payout, null=True, blank=True, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=20)
    amount_paise = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    ---

## Balance Calculation Query
from django.db.models import Sum

LedgerEntry.objects.filter(
    merchant=merchant,
    entry_type="credit"
).aggregate(total=Sum("amount_paise"))

## Available Balance Formula
available = credits + releases - holds
Why no debit subtraction?

Because hold already removed available money.

When payout completes:

hold already blocked funds
debit finalizes settlement

Subtracting debit again causes double deduction.


 ## Held Balance Formula
 held = holds - debits - releases

 ---
 ## 2. The Lock
 To stop two simultaneous withdrawals using same money:

Example:

balance ₹100
request A = ₹60
request B = ₹60

Only one should succeed.

What DB primitive used?
select_for_update()
This creates row-level lock in PostgreSQL.

Second request waits until first transaction finishes.

So race condition is prevented.

## 3. Idempotency
Clients may retry request due to network timeout.

Without idempotency:

same payout may happen twice.

## Header Used
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000

UniqueConstraint(
    fields=["merchant", "idempotency_key"],
    name="uniq_merchant_idem"
)

## Logic

If same merchant sends same key again:

Return existing payout response.

No duplicate payout created.

If first request in-flight?

## Second request waits due to DB transaction.

Then existing payout is returned.

Safe under concurrency.

## 4. State Machine

Allowed transitions:

pending -> processing -> completed
pending -> processing -> failed

Blocked:

completed -> pending
failed -> completed
completed -> failed

---

## 5. Failed Payout Refund Logic

If bank rejects payout:

Funds must return atomically.

with transaction.atomic():
    payout.status = "failed"
    payout.save()

   LedgerEntry.objects.create(
        merchant=payout.merchant,
        payout=payout,
        entry_type="release",
        amount_paise=payout.amount_paise
    )
    ---
## 6. Retry Logic

If payout stuck in processing > 30 sec:

retry with exponential backoff
max 3 attempts
then fail permanently
release funds

## Example:

retry 1 = 30 sec
retry 2 = 60 sec
retry 3 = 120 sec

After max retries:

status = failed
release funds'
----
## 7. Background Worker

Celery worker picks pending payouts.

Random simulation:

70% completed
20% failed
10% processing/hang

Example:

r = random.randint(1, 100)

if r <= 70:
    completed
elif r <= 90:
    failed
else:
    processing

----
## 8. API Endpoints
Dashboard
GET /api/v1/dashboard?merchant_id=1

Response:

{
  "available_balance": 230000,
  "held_balance": 0,
  "recent_payouts": []
}
Create Payout
POST /api/v1/payouts

Body:

{
  "merchant_id": 1,
  "amount_paise": 50000,
  "bank_account_id": 1
}
9. Tests Added
Concurrency Test

Two ₹60 requests against ₹100 balance.

Expected:

one success
one rejected
Idempotency Test

Same request twice with same key.

Expected:

same payout id returned
one DB row only
---

## 10. AI Audit

AI initially suggested:

if balance >= amount:
    create payout
    balance -= amount

Problem:

Two requests can pass same check simultaneously.

This causes overdraft.

Fixed Version

Used:

transaction.atomic()
select_for_update()
ledger rows

This guarantees safe concurrent payouts.
----

## 11. What I’m Most Proud Of
Correct money ledger design
Prevented race conditions
Proper idempotency
Async payout worker
Production deployable architecture

---

## 12. Future Improvements
Webhook callbacks
Better monitoring
Fraud checks
Bank API integration
Statement downloads
Audit dashboard

---

## 13. Deployment Notes
Build Command
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
Start Command
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120

----
# Playto Payout Engine - Full Setup Guide

A full-stack payout engine built with:

- **Backend:** Django + Django REST Framework
- **Frontend:** React + Tailwind CSS
- **Database:** PostgreSQL / SQLite
- **Background Jobs:** Celery + Redis
- **Deployment:** Render / Railway / Vercel

---

# Project Structure

text
play-to/
├── backend/      # Django Backend
├── frontend/     # React Frontend
└── README.md

## Features
Merchant Dashboard
Available Balance
Held Balance
Request Payout
Recent Payout History
Idempotency Key Support
Background Payout Processing
PostgreSQL Ready
Production Deployment Ready

## 1. Clone Project
git clone https://github.com/subramanyamchoda/play-to.git
cd play-to

## 2. Backend Setup (Django)
Go to backend
cd backend

## Create Virtual Environment
Windows
python -m venv env
env\Scripts\activate

## Install Requirements
pip install -r requirements.txt
Run Migrations
python manage.py migrate
Create Superuser (Optional)
python manage.py createsuperuser
Run Backend Server
python manage.py runserver

## Backend URL:

http://127.0.0.1:8000

3. Frontend Setup (React)

Open new terminal:

cd frontend

Install packages:

npm install

Run React App:

npm run dev

Frontend URL:

http://localhost:5173
4. Connect React with Django

Create file:

frontend/src/api.js

Paste:

import axios from "axios";

export default axios.create({
  baseURL: "http://127.0.0.1:8000/api",
});
5. API Endpoints
Dashboard
GET /api/v1/dashboard?merchant_id=1
Create Payout
POST /api/v1/payouts

Headers:

Idempotency-Key: unique-uuid

Body:

{
  "merchant_id": 1,
  "amount_paise": 50000,
  "bank_account_id": 1
}
