import random
import time
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils.timezone import now

from .models import LedgerEntry, Payout
from .state import transition


@shared_task(bind=True, max_retries=0)
def process_payout(self, payout_id: str):
    with transaction.atomic():
        try:
            payout = Payout.objects.select_for_update().get(pk=payout_id)
        except Payout.DoesNotExist:
            return
        if payout.status != Payout.STATUS_PENDING:
            return

        payout.attempts += 1
        payout.processing_started_at = now()
        transition(payout, Payout.STATUS_PROCESSING, save=False)
        payout.save(update_fields=["status", "attempts", "processing_started_at", "updated_at"])

    r = random.random()
    if r < 0.70:
        outcome = "success"
    elif r < 0.90:
        outcome = "failure"
    else:
        time.sleep(35)
        outcome = "failure"

    if outcome == "success":
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(pk=payout_id)
            if payout.status != Payout.STATUS_PROCESSING:
                return
            transition(payout, Payout.STATUS_COMPLETED)
    else:
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(pk=payout_id)
            if payout.status != Payout.STATUS_PROCESSING:
                return
            transition(payout, Payout.STATUS_FAILED)
            LedgerEntry.objects.create(
                merchant=payout.merchant,
                type=LedgerEntry.TYPE_CREDIT,
                amount_paise=payout.amount_paise,
                payout=payout,
                note="payout refund",
            )


@shared_task
def reap_stuck_payouts():
    cutoff = now() - timedelta(seconds=30)
    with transaction.atomic():
        stuck = Payout.objects.select_for_update(skip_locked=True).filter(
            status=Payout.STATUS_PROCESSING,
            processing_started_at__lt=cutoff,
        )

        for payout in stuck:
            if payout.attempts < 3:
                payout.attempts += 1
                transition(payout, Payout.STATUS_PENDING, save=False)
                payout.save(update_fields=["status", "attempts", "updated_at"])
                transaction.on_commit(
                    lambda payout_id=str(payout.id), retry_count=payout.attempts: process_payout.apply_async(
                        args=[payout_id], countdown=2 ** retry_count
                    )
                )
            else:
                transition(payout, Payout.STATUS_FAILED)
                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    type=LedgerEntry.TYPE_CREDIT,
                    amount_paise=payout.amount_paise,
                    payout=payout,
                    note="payout refund - max retries exceeded",
                )
