# Playto Founding Engineer Challenge – README

A minimal payout engine built to simulate how real payment systems safely process merchant withdrawals.

## Tech Stack

- **Backend:** Django + Django REST Framework  
- **Frontend:** React + Tailwind CSS  
- **Database:** PostgreSQL (SQLite for local dev optional)  
- **Background Jobs:** Celery + Redis  
- **Deployment:** Render / Railway / Vercel  

---

# Overview

This project allows merchants to:

- View balances
- Request payouts
- Prevent overdrafts
- Handle duplicate API retries
- Process payouts asynchronously
- Maintain accurate ledger records
- View recent payout history

---

# Why This Project Matters

Payout systems must be reliable. If two requests happen at the same time or a network retry occurs, money should never be deducted twice.

This project focuses on solving those real-world backend problems.

---

# Core Architecture

## Immutable Ledger System

Instead of storing one editable balance field, every money movement creates a new ledger entry.

### Entry Types

- `credit` → money added
- `hold` → payout requested, amount reserved
- `debit` → payout completed
- `release` → failed payout refunded

### Benefits

- Full audit trail
- Safer accounting
- Easy reconciliation
- Prevents hidden balance corruption

---

# Balance Logic

## Available Balance

```text
available = credits + releases - holds

```
Held Balance
held = holds - debits - releases
Race Condition Protection

If balance is ₹100 and two ₹60 payout requests arrive together, only one should succeed.

Used:

select_for_update()
transaction.atomic()

This creates row-level locking in PostgreSQL so simultaneous withdrawals cannot overspend funds.

Idempotency Protection

Clients may retry API calls if the internet fails.

Without idempotency, duplicate payouts may happen.

Header Used
Idempotency-Key: unique-uuid-value
Rule

If same merchant sends same key again:

Existing payout is returned
No duplicate row created
Payout State Machine

Allowed transitions:

pending -> processing -> completed
pending -> processing -> failed

Blocked transitions:

completed -> pending
completed -> failed
failed -> completed
Failed Payout Refund Flow

If payout fails:

Mark payout as failed
Create release ledger entry
Funds return to merchant balance

All done inside one transaction.

Retry Logic

If payout remains stuck:

Retry with exponential backoff
Maximum 3 attempts

Example:

Retry 1 = 30 sec
Retry 2 = 60 sec
Retry 3 = 120 sec

After max retries:

status = failed
funds released
Background Worker

Celery worker processes pending payouts asynchronously.

Simulation:

70% success
20% fail
10% delayed / stuck
API Endpoints
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

Headers:

Idempotency-Key: unique-uuid

Body:

{
  "merchant_id": 1,
  "amount_paise": 50000,
  "bank_account_id": 1
}
Tests Included
Concurrency Test

Two ₹60 payout requests against ₹100 balance.

Expected:

One succeeds
One rejected
Idempotency Test

Same request sent twice using same key.

Expected:

Same payout ID returned
Only one DB record created
AI Audit Improvement

Naive logic:

if balance >= amount:
    create_payout()
    balance -= amount

Problem:

Two requests may pass at same time.

Fixed with:

transaction.atomic()
select_for_update()
ledger entries
Local Setup Guide
Clone Project
git clone https://github.com/subramanyamchoda/play-to.git
cd play-to
Backend Setup
cd backend
python -m venv env
Activate Environment
Windows
env\Scripts\activate
Linux / Mac
source env/bin/activate
Install Packages
pip install -r requirements.txt
Run Migrations
python manage.py migrate
Create Admin (Optional)
python manage.py createsuperuser
Start Backend
python manage.py runserver

Backend URL:

http://127.0.0.1:8000
Frontend Setup

Open new terminal:

cd frontend
npm install
npm run dev

Frontend URL:

http://localhost:5173
Frontend API Config

Create:

frontend/src/api.js

Add:

import axios from "axios";

export default axios.create({
  baseURL: "http://127.0.0.1:8000/api",
});
Deployment
Build Command
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
Start Command
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
Future Improvements
Bank API integration
Webhook callbacks
Fraud detection
Better monitoring
Statements export
Admin analytics dashboard
