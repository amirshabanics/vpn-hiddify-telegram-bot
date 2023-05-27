from django.db import models

from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager
from users.models import User
import datetime


class Payment(CreateUpdateTracker):
    class PaymentStatus(models.TextChoices):
        FAILURE = "FAILURE"
        IN_PROGRESS = "IN_PROGRESS"
        SUCCESS = "SUCCESS"

    status = models.CharField(max_length=64, choices=PaymentStatus.choices, default=PaymentStatus.IN_PROGRESS)
    amount = models.FloatField(null=False)
    amount_after_discount = models.FloatField(null=False)
    user = models.ForeignKey(User, related_name="payments", null=False, on_delete=models.PROTECT)

    @property
    def expired_after(self):
        expired = 10 - (datetime.datetime.now(tz=datetime.timezone.utc) - self.created_at).total_seconds() / 60

        return expired if expired > 0 else 0


class Transaction(CreateUpdateTracker):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=False)
    amount = models.FloatField(null=False)


class DepositTransaction(CreateUpdateTracker):
    class DepositTransactionStatus(models.TextChoices):
        PAYED = "PAYED"
        PAYED_AND_CONFIRMED = "PAYED_AND_CONFIRMED"

    status = models.CharField(
        max_length=64,
        choices=DepositTransactionStatus.choices,
        default=DepositTransactionStatus.PAYED,
    )
    amount = models.FloatField(null=False)
    to_address = models.TextField(null=False)
    trx_hash = models.TextField()
    user = models.ForeignKey("users.User", related_name="deposits", on_delete=models.PROTECT)

