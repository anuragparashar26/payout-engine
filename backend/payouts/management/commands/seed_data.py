import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework.authtoken.models import Token

from payouts.balance import get_balance
from payouts.models import BankAccount, LedgerEntry, Merchant


SEED_MERCHANTS = [
    {
        "name": "Ravi Textiles",
        "token": "ravi-token-dev",
        "account_number": "0011223344556677",
        "ifsc": "HDFC0001234",
    },
    {
        "name": "Priya Design Co",
        "token": "priya-token-dev",
        "account_number": "0099887766554433",
        "ifsc": "ICIC0001234",
    },
    {
        "name": "Mehul Exports",
        "token": "mehul-token-dev",
        "account_number": "0011002299334411",
        "ifsc": "SBIN0001234",
    },
]


class Command(BaseCommand):
    help = "Seed merchants, bank accounts, tokens, and ledger entries"

    def handle(self, *args, **options):
        for row in SEED_MERCHANTS:
            merchant, _ = Merchant.objects.get_or_create(name=row["name"])

            BankAccount.objects.get_or_create(
                merchant=merchant,
                account_number=row["account_number"],
                defaults={
                    "ifsc": row["ifsc"],
                    "name": f"{merchant.name} Primary",
                    "is_primary": True,
                },
            )

            existing_credits = LedgerEntry.objects.filter(
                merchant=merchant,
                type=LedgerEntry.TYPE_CREDIT,
                note__startswith="seed credit",
            ).count()
            credits_needed = max(0, random.randint(8, 10) - existing_credits)
            for i in range(credits_needed):
                credit = LedgerEntry.objects.create(
                    merchant=merchant,
                    type=LedgerEntry.TYPE_CREDIT,
                    amount_paise=random.randint(10_000, 500_000),
                    note=f"seed credit {existing_credits + i + 1}",
                )
                days_ago = random.randint(0, 30)
                ts = timezone.now() - timedelta(days=days_ago)
                LedgerEntry.objects.filter(pk=credit.pk).update(created_at=ts)

            user, _ = User.objects.get_or_create(
                username=str(merchant.id),
                defaults={"first_name": merchant.name},
            )
            user.first_name = merchant.name
            user.save(update_fields=["first_name"])

            token, _ = Token.objects.get_or_create(user=user)
            if token.key != row["token"]:
                Token.objects.filter(user=user).delete()
                token = Token.objects.create(user=user, key=row["token"])

            balance = get_balance(str(merchant.id))
            bank_account = merchant.bank_accounts.first()
            rupees = balance["total_paise"] / 100
            self.stdout.write(
                f"{merchant.name} | {token.key} | INR {rupees:,.2f} | {bank_account.account_number}"
            )
