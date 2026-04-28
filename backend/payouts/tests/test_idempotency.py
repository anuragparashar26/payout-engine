import pytest
from rest_framework.test import APIClient

from payouts.models import LedgerEntry, Payout


@pytest.mark.django_db
def test_same_key_returns_same_response(merchant, bank_account, auth_token, idempotency_key):
    LedgerEntry.objects.create(
        merchant=merchant,
        type=LedgerEntry.TYPE_CREDIT,
        amount_paise=300_000,
        note="seed balance",
    )

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    payload = {
        "amount_paise": 50_000,
        "bank_account_id": str(bank_account.id),
    }

    first = client.post(
        "/api/v1/payouts/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idempotency_key,
    )
    second = client.post(
        "/api/v1/payouts/",
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idempotency_key,
    )

    assert Payout.objects.filter(merchant=merchant).count() == 1
    assert first.content == second.content
    assert first.status_code == 201
    assert second.status_code == 201
