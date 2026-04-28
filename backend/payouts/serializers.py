from rest_framework import serializers

from .models import BankAccount, LedgerEntry, Payout


class PayoutCreateSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.UUIDField()


class PayoutSerializer(serializers.ModelSerializer):
    bank_account_name = serializers.CharField(source="bank_account.name", read_only=True)

    class Meta:
        model = Payout
        fields = [
            "id",
            "amount_paise",
            "status",
            "attempts",
            "processing_started_at",
            "created_at",
            "updated_at",
            "bank_account",
            "bank_account_name",
        ]


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ["id", "type", "amount_paise", "note", "created_at", "payout"]


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id", "account_number", "ifsc", "name", "is_primary"]
