from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from payouts.models import BankAccount, Merchant


@pytest.fixture
def merchant(db):
    return Merchant.objects.create(name="Test Merchant")


@pytest.fixture
def bank_account(db, merchant):
    return BankAccount.objects.create(
        merchant=merchant,
        account_number="123456789012",
        ifsc="HDFC0000001",
        name="Test Merchant Primary",
        is_primary=True,
    )


@pytest.fixture
def auth_token(db, merchant):
    user = get_user_model().objects.create_user(username=str(merchant.id), password="pass12345")
    token = Token.objects.create(user=user)
    return token


@pytest.fixture(autouse=True)
def disable_enqueue(monkeypatch):
    from payouts import tasks

    monkeypatch.setattr(tasks.process_payout, "apply_async", lambda *args, **kwargs: None)


@pytest.fixture
def idempotency_key():
    return str(uuid4())
