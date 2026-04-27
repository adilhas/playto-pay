from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from payouts.models import Payout
from payouts.services import process_payout
from django.db import transaction
from ledger.models import LedgerEntry


@shared_task
def process_payout_task(payout_id):
    process_payout(payout_id)


@shared_task
def retry_stuck_payouts():
    threshold = timezone.now() - timedelta(seconds=30)

    stuck_payouts = Payout.objects.filter(
        status="processing", last_attempt_at__lt=threshold
    )

    for payout in stuck_payouts:
        if payout.retry_count >= 3:
            with transaction.atomic():
                payout.transition_to("failed")

                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    amount_paise=payout.amount_paise,
                    transaction_type="credit",
                    reference_type="payout_refund",
                    reference_id=payout.id,
                )
        else:
            # retry
            process_payout_task.delay(payout.id)
