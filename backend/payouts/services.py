from django.db.models import Sum
from .models import LedgerEntry


def _sum_entries(merchant, entry_type):
    total = (
        LedgerEntry.objects.filter(
            merchant=merchant,
            entry_type=entry_type
        ).aggregate(total=Sum("amount_paise"))["total"]
    )
    return total or 0


def get_total_credits(merchant):
    return _sum_entries(merchant, "credit")


def get_total_holds(merchant):
    return _sum_entries(merchant, "hold")


def get_total_debits(merchant):
    return _sum_entries(merchant, "debit")


def get_total_releases(merchant):
    return _sum_entries(merchant, "release")


def get_available_balance(merchant):
    credits = get_total_credits(merchant)
    holds = get_total_holds(merchant)
    releases = get_total_releases(merchant)

    # hold already reduced funds
    return max(credits + releases - holds, 0)


def get_held_balance(merchant):
    holds = get_total_holds(merchant)
    debits = get_total_debits(merchant)
    releases = get_total_releases(merchant)

    return max(holds - debits - releases, 0)


def get_balance_summary(merchant):
    return {
        "credits": get_total_credits(merchant),
        "holds": get_total_holds(merchant),
        "debits": get_total_debits(merchant),
        "releases": get_total_releases(merchant),
        "available_balance": get_available_balance(merchant),
        "held_balance": get_held_balance(merchant),
    }