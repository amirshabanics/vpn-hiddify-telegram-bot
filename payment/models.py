from django.db import models

# Create your models here.
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager


class Payment(CreateUpdateTracker):
    class PaymentStatus(models.TextChoices):
        FAILURE = "FAILURE"
        IN_PROGRESS = "IN_PROGRESS"
        SUCCESS = "SUCCESS"

    status = models.CharField(max_length=64, choices=PaymentStatus.choices, default=PaymentStatus.IN_PROGRESS)
    amount = models.PositiveBigIntegerField(null=False)
    amount_after_discount = models.PositiveBigIntegerField(null=False)


class Transaction(CreateUpdateTracker):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=False)
    amount = models.PositiveBigIntegerField(null=False)


class DepositTransaction(CreateUpdateTracker):
    class DepositTransactionStatus(models.TextChoices):
        PAYED = "PAYED"
        PAYED_AND_CONFIRMED = "PAYED_AND_CONFIRMED"

    status = models.CharField(
        max_length=64,
        choices=DepositTransactionStatus.choices,
        default=DepositTransactionStatus.PAYED,
    )
    amount = models.PositiveBigIntegerField(null=False)
    to_address = models.TextField(null=False)
    trx_hash = models.TextField()
