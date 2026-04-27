import random

from payouts.models import Payout
from django.utils import timezone


def process_payout(payout_id):
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return

    if payout.status not in ["pending", "processing"]:
        return

    if payout.status == "pending":
        payout.transition_to("processing")

    # retry metadata update
    payout.retry_count += 1
    payout.last_attempt_at = timezone.now()
    payout.save(update_fields=["retry_count", "last_attempt_at"])

    outcome = random.random()

    if outcome < 0.7:
        payout.transition_to("completed")

    elif outcome < 0.9:
        from django.db import transaction
        from ledger.models import LedgerEntry

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
        # stuck → remain in processing
        pass
