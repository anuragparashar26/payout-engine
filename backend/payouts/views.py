from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .balance import get_balance
from .models import BankAccount, IdempotencyKey, LedgerEntry, Merchant, Payout
from .serializers import (
	BankAccountSerializer,
	LedgerEntrySerializer,
	PayoutCreateSerializer,
	PayoutSerializer,
)


def current_merchant(request):
	return Merchant.objects.get(pk=request.user.username)


class PayoutListCreateView(APIView):
	def get(self, request):
		merchant = current_merchant(request)
		queryset = Payout.objects.filter(merchant=merchant).order_by("-created_at")[:50]
		return Response(PayoutSerializer(queryset, many=True).data)

	def post(self, request):
		merchant = current_merchant(request)

		idempotency_key = request.headers.get("Idempotency-Key")
		if not idempotency_key:
			return Response({"error": "missing_idempotency_key"}, status=status.HTTP_400_BAD_REQUEST)

		existing = IdempotencyKey.objects.filter(
			merchant=merchant,
			key=idempotency_key,
			expires_at__gt=now(),
		).first()
		if existing:
			return Response(existing.response_body, status=existing.status_code)

		serializer = PayoutCreateSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		amount_paise = serializer.validated_data["amount_paise"]
		bank_account_id = serializer.validated_data["bank_account_id"]

		bank_account = BankAccount.objects.filter(id=bank_account_id, merchant=merchant).first()
		if not bank_account:
			return Response({"error": "invalid_bank_account"}, status=status.HTTP_400_BAD_REQUEST)

		if amount_paise <= 0:
			return Response({"error": "invalid_amount"}, status=status.HTTP_400_BAD_REQUEST)

		with transaction.atomic():
			merchant_row = Merchant.objects.select_for_update().get(pk=merchant.pk)
			balance = get_balance(str(merchant_row.pk))
			if amount_paise > balance["available_paise"]:
				return Response({"error": "insufficient_funds"}, status=402)

			payout = Payout.objects.create(
				merchant=merchant_row,
				bank_account=bank_account,
				amount_paise=amount_paise,
				status=Payout.STATUS_PENDING,
			)
			LedgerEntry.objects.create(
				merchant=merchant_row,
				type=LedgerEntry.TYPE_DEBIT,
				amount_paise=amount_paise,
				payout=payout,
				note="payout request",
			)

			from .tasks import process_payout

			transaction.on_commit(lambda: process_payout.apply_async(args=[str(payout.id)]))

		response_data = {
			"id": str(payout.id),
			"merchant_id": str(merchant.pk),
			"amount_paise": payout.amount_paise,
			"status": payout.status,
			"attempts": payout.attempts,
			"bank_account_id": str(bank_account.id),
			"created_at": payout.created_at.isoformat().replace("+00:00", "Z"),
		}

		try:
			saved_key = IdempotencyKey.objects.create(
				merchant=merchant,
				key=idempotency_key,
				response_body=response_data,
				status_code=201,
				expires_at=now() + timedelta(hours=24),
			)
			payout.idempotency_key = saved_key
			payout.save(update_fields=["idempotency_key", "updated_at"])
			return Response(response_data, status=201)
		except IntegrityError:
			saved = IdempotencyKey.objects.get(
				merchant=merchant,
				key=idempotency_key,
				expires_at__gt=now(),
			)
			return Response(saved.response_body, status=saved.status_code)


class BalanceView(APIView):
	def get(self, request):
		merchant = current_merchant(request)
		return Response(get_balance(str(merchant.pk)))


class PayoutDetailView(APIView):
	def get(self, request, payout_id):
		merchant = current_merchant(request)
		payout = Payout.objects.filter(id=payout_id, merchant=merchant).first()
		if not payout:
			return Response({"error": "not_found"}, status=404)
		return Response(PayoutSerializer(payout).data)


class LedgerListView(APIView):
	def get(self, request):
		merchant = current_merchant(request)
		queryset = LedgerEntry.objects.filter(merchant=merchant).order_by("-created_at")[:50]
		return Response(LedgerEntrySerializer(queryset, many=True).data)


class BankAccountListView(APIView):
	def get(self, request):
		merchant = current_merchant(request)
		queryset = BankAccount.objects.filter(merchant=merchant).order_by("-is_primary", "name")
		return Response(BankAccountSerializer(queryset, many=True).data)
