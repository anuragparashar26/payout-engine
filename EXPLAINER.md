# EXPLAINER.md

## 1. The Ledger

### Balance Calculation Query

```python
def get_balance(merchant_id: str) -> dict:
    row = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
        credits=Sum("amount_paise", filter=Q(type="credit")),
        debits=Sum("amount_paise", filter=Q(type="debit")),
    )
    credits = row["credits"] or 0
    debits = row["debits"] or 0
    total_paise = credits - debits
    held_paise = (
        Payout.objects.filter(merchant_id=merchant_id, status__in=["pending", "processing"]).aggregate(
            h=Sum("amount_paise")
        )["h"]
        or 0
    )
    return {
        "total_paise": total_paise,
        "held_paise": held_paise,
        "available_paise": total_paise - held_paise,
    }
```

### Why This Model?

Credits and debits are stored as separate LedgerEntry rows, not as a balance field. This is the double-entry accounting pattern - every transaction creates an immutable record. The balance is always derived via `SUM()` aggregation, never stored. This guarantees the invariant: credits minus debits always equals displayed balance. There's no way to manually set a balance that doesn't match the ledger.

---

## 2. The Lock

### Concurrency Protection Code

```python
with transaction.atomic():
    merchant_row = Merchant.objects.select_for_update().get(pk=merchant.pk)
    balance = get_balance(str(merchant_row.pk))
    if amount_paise > balance["available_paise"]:
        return Response({"error": "insufficient_funds"}, status=402)
```

### Database Primitive

`SELECT FOR UPDATE` acquires a row-level lock on the merchant row within the transaction. When two concurrent requests arrive:

1. Request A acquires lock on merchant row, reads balance
2. Request B blocks waiting for the lock
3. Request A creates payout, commits, releases lock
4. Request B acquires lock, reads balance (which now reflects the held funds), rejects

The lock is acquired BEFORE balance calculation, preventing any race window between check and deduct. This uses PostgreSQL's MVCC - the lock blocks other transactions from reading the row until released.

---

## 3. The Idempotency

### How It Works

```python
existing = IdempotencyKey.objects.filter(
    merchant=merchant,
    key=idempotency_key,
    expires_at__gt=now(),
).first()
if existing:
    return Response(existing.response_body, status=existing.status_code)
```

Keys are stored with an expiry (24 hours). Before creating a payout, we check for an existing, unexpired key for this merchant.

### What If First Request Is In Flight?

This is the tricky case. If Request A is processing (not yet committed) and Request B arrives:

1. No existing key found for both A and B
2. Both proceed to create payout
3. Both try to create IdempotencyKey
4. Database unique constraint on `(merchant, key)` catches this

The `unique_together = [("merchant", "key")]` constraint in the model throws IntegrityError, which we catch:

```python
try:
    saved_key = IdempotencyKey.objects.create(...)
except IntegrityError:
    saved = IdempotencyKey.objects.get(...)
    return Response(saved.response_body, status=saved.status_code)
```

This guarantees exactly-once semantics even under concurrent requests.

---

## 4. The State Machine

### Illegal Transition Blocking

```python
VALID_TRANSITIONS = {
    "pending": ["processing"],
    "processing": ["completed", "failed", "pending"],
}

def transition(payout, new_status: str, save: bool = True) -> None:
    allowed = VALID_TRANSITIONS.get(payout.status, [])
    if new_status not in allowed:
        raise ValueError(f"Illegal transition: {payout.status} -> {new_status}")
```

The state machine is enforced at the model layer. The worker calls `transition()` which validates against VALID_TRANSITIONS. A transition from "failed" to "completed" is impossible because "failed" has no allowed targets.

Additionally, the worker's processing loop checks current status before transitioning:

```python
if payout.status != Payout.STATUS_PROCESSING:
    return
transition(payout, Payout.STATUS_COMPLETED)
```

This double-checks in case another process modified the state while we were working.

---

## 5. The AI Audit

### Example: Race Condition in Initial Balance Calculation

**AI's Wrong Code:**
```python
balance = get_balance(str(merchant.pk))
if amount_paise > balance["available_paise"]:
    return Response({"error": "insufficient_funds"}, status=402)
```

This reads balance WITHOUT holding the lock. Between the read and the payout creation, another request could spend the funds.

**What I Caught:**
The balance check happens outside the transaction block. In concurrent scenarios, both requests read the same balance before either writes.

**What I Replaced It With:**
```python
with transaction.atomic():
    merchant_row = Merchant.objects.select_for_update().get(pk=merchant.pk)
    balance = get_balance(str(merchant_row.pk))
    if amount_paise > balance["available_paise"]:
        return Response({"error": "insufficient_funds"}, status=402)
    # ... create payout
```

The entire check-and-create happens within a single `transaction.atomic()` with `SELECT FOR UPDATE` locking the merchant row first. No race window exists.

---

## Additional Notes

### Why BigIntegerField?

Floats cause precision errors (e.g., 0.1 + 0.2 != 0.3). Money in India is counted in paise (1/100 of a rupee). Using BigIntegerField stores exact integer values. All amounts are in paise internally, converted only at display time.

### Why Not Django's F() Expressions for Balance?

We considered `LedgerEntry.objects.annotate(balance=Sum(F('amount')))` but it doesn't handle the "held funds" calculation. We need balance minus pending payouts. The current approach using separate queries with SUM aggregation is clearer and testable.

### Retry Logic

Payouts stuck in "processing" for >30 seconds are retried by `reap_stuck_payouts` task with exponential backoff (2^attempt seconds). After 3 attempts, it permanently fails and refunds. This is implemented in `tasks.py:reap_stuck_payouts()`.