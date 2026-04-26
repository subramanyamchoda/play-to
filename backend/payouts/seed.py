from payouts.models import (
    Merchant,
    BankAccount,
    LedgerEntry
)


def run():
    """
    Seed sample merchants with balances.
    Safe to re-run (won't duplicate by email).
    """

    merchants = [
        {
            "name": "Rahul Agency",
            "email": "rahul@test.com",
            "holder_name": "Rahul",
            "account_number": "1234567890",
            "ifsc": "HDFC0001",
            "credit": 100000,   # ₹1000
        },
        {
            "name": "Aman Freelance",
            "email": "aman@test.com",
            "holder_name": "Aman",
            "account_number": "2222222222",
            "ifsc": "ICICI0002",
            "credit": 250000,   # ₹2500
        },
        {
            "name": "Sita Digital",
            "email": "sita@test.com",
            "holder_name": "Sita",
            "account_number": "3333333333",
            "ifsc": "SBIN0003",
            "credit": 500000,   # ₹5000
        },
    ]

    for item in merchants:
        merchant, created = Merchant.objects.get_or_create(
            email=item["email"],
            defaults={
                "name": item["name"]
            }
        )

        BankAccount.objects.get_or_create(
            merchant=merchant,
            account_number=item["account_number"],
            defaults={
                "holder_name": item["holder_name"],
                "ifsc": item["ifsc"],
                "is_active": True
            }
        )

        # Add credit only if no ledger exists
        if not LedgerEntry.objects.filter(
            merchant=merchant,
            entry_type="credit"
        ).exists():

            LedgerEntry.objects.create(
                merchant=merchant,
                entry_type="credit",
                amount_paise=item["credit"],
                reference="seed_credit"
            )

    print("Seed data inserted successfully.")