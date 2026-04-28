import threading
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from payouts.models import LedgerEntry, Payout


@pytest.mark.django_db(transaction=True)
def test_two_concurrent_payouts_only_one_succeeds(merchant, bank_account, auth_token):
    LedgerEntry.objects.create(
        merchant=merchant,
        type=LedgerEntry.TYPE_CREDIT,
        amount_paise=100_000,
        note="seed balance",
    )

    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(2)

    def fire_once():
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")
        barrier.wait()
        response = client.post(
            "/api/v1/payouts/",
            {
                "amount_paise": 60_000,
                "bank_account_id": str(bank_account.id),
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )
        with lock:
            results.append(response.status_code)

    t1 = threading.Thread(target=fire_once)
    t2 = threading.Thread(target=fire_once)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert Payout.objects.filter(merchant=merchant).count() == 1
    assert sorted(results) == [201, 402]
