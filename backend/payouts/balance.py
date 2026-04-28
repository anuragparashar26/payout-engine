from django.db.models import Q, Sum

from .models import LedgerEntry, Payout


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
