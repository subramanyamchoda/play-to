import random

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Payout, LedgerEntry


# Legal state transitions only
ALLOWED = {
    "pending": ["processing"],
    "processing": ["completed", "failed"],
    "completed": [],
    "failed": [],
}


def move_status(payout, new_status):
    """
    Enforce payout state machine.
    """
    current = payout.status

    if new_status not in ALLOWED.get(current, []):
        raise ValueError(
            f"Illegal transition {current} -> {new_status}"
        )

    payout.status = new_status
    payout.save(update_fields=["status", "updated_at"])


@shared_task
def process_payout(payout_id):
    """
    Main async processor.
    Simulates bank settlement:
    70% success
    20% fail
    10% stuck -> retry
    """
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return

    # Move pending -> processing
    if payout.status == "pending":
        move_status(payout, "processing")

    elif payout.status != "processing":
        return

    roll = random.randint(1, 100)

    if roll <= 70:
        complete_payout.delay(payout.id)

    elif roll <= 90:
        fail_payout.delay(payout.id)

    else:
        retry_processing.delay(payout.id)


@shared_task
def complete_payout(payout_id):
    """
    Final successful payout.
    Creates debit ledger entry.
    """
    with transaction.atomic():
        try:
            payout = (
                Payout.objects
                .select_for_update()
                .get(id=payout_id)
            )
        except Payout.DoesNotExist:
            return

        if payout.status != "processing":
            return

        move_status(payout, "completed")

        LedgerEntry.objects.create(
            merchant=payout.merchant,
            entry_type="debit",
            amount_paise=payout.amount_paise,
            reference=f"payout:{payout.id}"
        )


@shared_task
def fail_payout(payout_id):
    """
    Failed payout.
    Refunds held funds atomically.
    """
    with transaction.atomic():
        try:
            payout = (
                Payout.objects
                .select_for_update()
                .get(id=payout_id)
            )
        except Payout.DoesNotExist:
            return

        if payout.status != "processing":
            return

        move_status(payout, "failed")

        # Return money
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            entry_type="release",
            amount_paise=payout.amount_paise,
            reference=f"refund:{payout.id}"
        )


@shared_task
def retry_processing(payout_id):
    """
    Retry stuck payouts with exponential backoff.
    Max 3 attempts.
    """
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return

    if payout.status != "processing":
        return

    payout.attempt_count += 1
    payout.save(update_fields=["attempt_count"])

    if payout.attempt_count >= 3:
        fail_payout.delay(payout.id)
        return

    # attempt1=10s, attempt2=20s
    delay_seconds = 5 * (2 ** payout.attempt_count)

    process_payout.apply_async(
        args=[payout.id],
        countdown=delay_seconds
    )