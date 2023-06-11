from django.db import models
import datetime
from payment.models import Payment
from users.models import User
from utils.models import CreateUpdateTracker, CreateTracker
from django.core.validators import MaxValueValidator, MinValueValidator


class HiddifyPanel(models.Model):
    domain = models.TextField(null=False)
    panel_id = models.TextField(null=False)
    admin_id = models.TextField(null=False)

    def __str__(self):
        return self.domain

    def get_vpn_link(self, vpn_uuid):
        return "https://{domain}/{panel_id}/{uuid}/".format(
            domain=self.domain,
            panel_id=self.panel_id,
            uuid=vpn_uuid,
        )

    def get_create_vpn_link(self):
        return "https://{domain}/{panel_id}/{admin_id}/admin/user/new/".format(
            domain=self.domain,
            panel_id=self.panel_id,
            admin_id=self.admin_id,
        )


class Subscription(CreateUpdateTracker):
    class SubscriptionMode(models.TextChoices):
        no_reset = "no_reset"
        daily = "daily"
        weekly = "weekly"
        monthly = "monthly"

    package_days = models.PositiveBigIntegerField(null=False, default=90)
    usage_limit = models.PositiveBigIntegerField(null=False, default=50, help_text="In GB")
    mode = models.CharField(
        null=False,
        default=SubscriptionMode.no_reset,
        choices=SubscriptionMode.choices,
        max_length=20,
    )
    amount = models.PositiveBigIntegerField(null=False, default=7)
    hiddify = models.ForeignKey(HiddifyPanel, on_delete=models.CASCADE, null=False)


class VPN(CreateUpdateTracker):
    link = models.TextField()
    user_uuid = models.TextField()
    user = models.ForeignKey(User, related_name="vpns", on_delete=models.CASCADE)
    active_days = models.PositiveBigIntegerField(default=90)
    payment = models.ForeignKey(Payment, related_name="vpns", null=False, on_delete=models.PROTECT)
    subscription = models.ForeignKey(Subscription, related_name="vpns", null=False, on_delete=models.PROTECT)

    @property
    def left_days(self):
        return self.active_days - (datetime.date.today() - self.created_at.date()).days


class Discount(CreateUpdateTracker):
    percentage = models.PositiveIntegerField(validators=[MaxValueValidator(100), MinValueValidator(1)], null=False)
    limit_per_user = models.IntegerField(null=False, default=-1)
    subscription = models.ForeignKey(Subscription, null=False, on_delete=models.CASCADE)

    def calculate_amount_after_discount(self, amount):
        return amount - amount * self.percentage / 100
