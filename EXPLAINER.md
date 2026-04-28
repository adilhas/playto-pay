# **Payout Engine System Design Explainer**

---

## **1\. Introduction**

This project implements a payout processing system using Django, Django REST Framework, PostgreSQL, and Celery.

The system is designed to handle payouts safely while ensuring:

- Concurrency safety (no double spending)
- Idempotency (no duplicate payouts)
- Fault tolerance (retry on failure)
- Strict state transitions

---

## **2\. Core Problem**

In real-world financial systems, payout processing must handle:

- Concurrent requests from multiple clients
- Network retries causing duplicate API calls
- External system failures
- Partial or delayed processing

This system is designed to solve these challenges while maintaining correctness.

---

## **3\. Ledger-Based Balance System**

Instead of storing balance as a mutable field, the system uses a **ledger-based approach**.

### **Balance Calculation**

```python
from django.db.models import Sum

balance \= LedgerEntry.objects.filter(merchant=merchant).aggregate(

   total=Sum("amount\_paise")

)\["total"\] or 0
```

### **Why This Design?**

- Every transaction is recorded → **fully auditable**
- No risk of inconsistent balance updates
- Refunds and reversals are simple (add new entries)
- Matches real-world financial systems

---

## **4\. Concurrency Control**

To prevent race conditions, the system uses database-level locking.

### **Code**

```python
from django.db import transaction

with transaction.atomic():

   merchant = Merchant.objects.select_for_update().get(id=merchant_id)

   balance = get_merchant_balance(merchant)

   if balance < amount:

       raise Exception("Insufficient balance")
```

### **Database Primitive Used**

SELECT ... FOR UPDATE

### **Why This Works**

- Locks the row until transaction completes
- Prevents concurrent updates
- Ensures only one payout can modify balance at a time

👉 Guarantees no double spending

---

## **5\. Idempotency**

Each payout request requires:

Idempotency-Key header

### **Detection Logic**

```python
existing_payout = Payout.objects.filter(

   merchant=merchant,

   idempotency_key=idempotency_key

).first()
```

### **Behavior**

- If key exists → return existing payout
- If not → create new payout

  ### **Concurrent Request Handling**

- Unique constraint on `(merchant, idempotency_key)`
- Wrapped inside `transaction.atomic()`

If two requests arrive at the same time:

1. Both attempt insert
2. One succeeds
3. Other raises `IntegrityError`
4. Second fetches existing payout

👉 Ensures **exactly-once payout creation**

---

## **6\. Async Processing with Celery**

Payout processing is handled asynchronously.

### **Flow**

API → create payout (pending) → enqueue Celery task → worker processes payout

### **Benefits**

- Fast API response
- Scalable processing
- Decoupled architecture

### **Deployment**

The system is deployed as a distributed architecture:

- Django API → hosted on Render
- Celery Worker → hosted on Railway
- Redis → hosted on Redis Cloud

The API enqueues payout tasks to Redis, and the Celery worker (running independently) consumes and processes them asynchronously.

This setup mirrors a real production system where background processing is handled by a separate worker service.

---

## **7\. Retry Mechanism**

Payouts may get stuck due to failures.

### **Strategy**

- Detect payouts stuck in `processing`
- Retry after 30 seconds
- Maximum 3 retries

### **Final Failure Handling**

If retries exceed limit:

- Mark payout as `failed`
- Create ledger refund entry

### **Result**

- No payout remains stuck
- Funds are never lost

---

## **8\. State Machine Enforcement**

Payout lifecycle is strictly controlled.

### **Allowed Transitions**

pending → processing → completed

pending → processing → failed

### **Implementation**

```python

def transition_to(self, new_status):

   allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])

   if new_status not in allowed:

       raise ValueError(

           f"Invalid transition: {self.status} → {new_status}"

       )

   self.status = new_status

   self.save(update_fields=["status"])
```

### **Protection**

- Invalid transitions raise errors
- Prevents state corruption

---

## **9\. Testing Strategy**

### **1\. Concurrency Test**

- Simulates parallel payout requests
- Ensures only one succeeds

### **2\. Idempotency Test**

- Same request sent twice
- Confirms same response is returned

---

## **10\. Tradeoffs**

| Decision         | Tradeoff                          |
| ---------------- | --------------------------------- |
| Ledger system    | More queries but safer            |
| Async processing | Eventual consistency              |
| Retry limit      | Some payouts may fail permanently |

---

## **11\. Critical Design Questions**

### **1\. The Ledger**

#### **Balance Query**

```python
  balance = LedgerEntry.objects.filter(merchant=merchant).aggregate(

     total=Sum("amount_paise")

  )["total"] or 0

  #### **Why Credits & Debits?**

```

- Positive → credit
- Negative → debit

**Reason:**

- Immutable transaction history
- Easy reconciliation
- No race conditions on balance

### **2\. The Lock**

```python

  with transaction.atomic():
     merchant = Merchant.objects.select_for_update().get(id=merchant\_id)
```

#### **Primitive**

SELECT FOR UPDATE

#### **Explanation**

- Locks row
- Prevents concurrent modifications
- Ensures safe balance check

### **3\. The Idempotency**

#### **Detection**

```python
  Payout.objects.filter(
     merchant=merchant,
     idempotency\_key=idempotency\_key
  ).first()
```

#### **Concurrent Behavior**

- Unique DB constraint
- One succeeds, one fails
- Failed one fetches existing payout

### **4\. The State Machine**

#### **Enforcement Code**

if new_status not in allowed:  
 raise ValueError

#### **Example**

failed → completed ❌ blocked

### **5\. The AI Audit**

#### **Incorrect AI Suggestion**

```python
  # ❌ WRONG
  merchant.balance -= amount
  merchant.save()

```

#### **Problem**

- Not concurrency-safe
- Race condition → double spending

#### **Fix**

```python
  with transaction.atomic():
     merchant = Merchant.objects.select_for_update().get(id=merchant.id)
```

#### **Another AI Mistake**

```python
  process_payout.delay(payout.id)  \# mistake

  #### **Fix**

  process_payout_task.delay(payout.id)  \# corected
```

#### **Takeaway**

AI helped speed development but required:

- validation
- system understanding
- debugging
