import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .tasks import process_payout
from .models import (
    Merchant,
    BankAccount,
    LedgerEntry,
    Payout,
    IdempotencyKey
)

from .serializers import (
    PayoutCreateSerializer,
    PayoutSerializer
)

from .services import (
    get_available_balance,
    get_held_balance
)


class CreatePayoutAPIView(APIView):

    @transaction.atomic
    def post(self, request):
        serializer = PayoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        merchant_id = serializer.validated_data["merchant_id"]
        amount = serializer.validated_data["amount_paise"]
        bank_account_id = serializer.validated_data["bank_account_id"]

        raw_key = request.headers.get("Idempotency-Key")

        if not raw_key:
            return Response(
                {"error": "Idempotency-Key header required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            key_uuid = uuid.UUID(raw_key)
        except ValueError:
            return Response(
                {"error": "Invalid UUID key"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Row lock to prevent concurrent overdraft
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)
        except Merchant.DoesNotExist:
            return Response(
                {"error": "Merchant not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Idempotency check
        existing = IdempotencyKey.objects.filter(
            merchant=merchant,
            key=key_uuid,
            expires_at__gt=timezone.now()
        ).first()

        if existing:
            return Response(existing.response_data, status=status.HTTP_200_OK)

        try:
            bank = BankAccount.objects.get(
                id=bank_account_id,
                merchant=merchant,
                is_active=True
            )
        except BankAccount.DoesNotExist:
            return Response(
                {"error": "Bank account not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        available = get_available_balance(merchant)

        if available < amount:
            return Response(
                {"error": "Insufficient balance"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create payout
        payout = Payout.objects.create(
            merchant=merchant,
            bank_account=bank,
            amount_paise=amount,
            status="pending"
        )

        # Hold funds
        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type="hold",
            amount_paise=amount,
            reference=f"payout:{payout.id}"
        )

        response_data = {
            "id": payout.id,
            "status": payout.status,
            "amount_paise": payout.amount_paise,
            "merchant_id": merchant.id
        }

        # Save idempotency key
        IdempotencyKey.objects.create(
            merchant=merchant,
            key=key_uuid,
            response_data=response_data,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # Run async worker after transaction commit
        transaction.on_commit(
            lambda: process_payout.delay(payout.id)
        )

        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


class DashboardAPIView(APIView):

    def get(self, request):
        merchant_id = request.query_params.get("merchant_id")

        if not merchant_id:
            return Response(
                {"error": "merchant_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            merchant = Merchant.objects.get(id=merchant_id)
        except Merchant.DoesNotExist:
            return Response(
                {"error": "Merchant not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = {
            "merchant": merchant.name,
            "available_balance": get_available_balance(merchant),
            "held_balance": get_held_balance(merchant),
            "recent_ledger": list(
                LedgerEntry.objects.filter(
                    merchant=merchant
                ).order_by("-id")[:10].values()
            ),
            "recent_payouts": list(
                Payout.objects.filter(
                    merchant=merchant
                ).order_by("-id")[:10].values()
            )
        }

        return Response(data, status=status.HTTP_200_OK)


class PayoutListAPIView(APIView):

    def get(self, request):
        merchant_id = request.query_params.get("merchant_id")

        if not merchant_id:
            return Response(
                {"error": "merchant_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payouts = Payout.objects.filter(
            merchant_id=merchant_id
        ).order_by("-id")

        serializer = PayoutSerializer(payouts, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )