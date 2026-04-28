from django.db import models
from django.utils import timezone
from uuid import uuid4


def default_idempotency_expiry():
	return timezone.now()


class Merchant(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
	name = models.CharField(max_length=120)
	created_at = models.DateTimeField(auto_now_add=True)


class BankAccount(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
	merchant = models.ForeignKey(Merchant, related_name="bank_accounts", on_delete=models.CASCADE)
	account_number = models.CharField(max_length=20)
	ifsc = models.CharField(max_length=11)
	name = models.CharField(max_length=120)
	is_primary = models.BooleanField(default=False)


class IdempotencyKey(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
	merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
	key = models.CharField(max_length=64)
	response_body = models.JSONField()
	status_code = models.PositiveSmallIntegerField()
	expires_at = models.DateTimeField(default=default_idempotency_expiry)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = [("merchant", "key")]


class Payout(models.Model):
	STATUS_PENDING = "pending"
	STATUS_PROCESSING = "processing"
	STATUS_COMPLETED = "completed"
	STATUS_FAILED = "failed"

	STATUS_CHOICES = [
		(STATUS_PENDING, "pending"),
		(STATUS_PROCESSING, "processing"),
		(STATUS_COMPLETED, "completed"),
		(STATUS_FAILED, "failed"),
	]

	id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
	merchant = models.ForeignKey(Merchant, related_name="payouts", on_delete=models.CASCADE)
	bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)
	amount_paise = models.BigIntegerField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	attempts = models.PositiveSmallIntegerField(default=0)
	processing_started_at = models.DateTimeField(null=True, blank=True)
	idempotency_key = models.ForeignKey(
		IdempotencyKey, null=True, blank=True, on_delete=models.SET_NULL
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


class LedgerEntry(models.Model):
	TYPE_CREDIT = "credit"
	TYPE_DEBIT = "debit"

	TYPE_CHOICES = [
		(TYPE_CREDIT, "credit"),
		(TYPE_DEBIT, "debit"),
	]

	id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
	merchant = models.ForeignKey(Merchant, related_name="ledger_entries", on_delete=models.CASCADE)
	type = models.CharField(max_length=10, choices=TYPE_CHOICES)
	amount_paise = models.BigIntegerField()
	payout = models.ForeignKey(
		Payout, null=True, blank=True, related_name="ledger_entries", on_delete=models.SET_NULL
	)
	note = models.CharField(max_length=200, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
