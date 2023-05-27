from django.db import models
import datetime
from payment.models import Payment
from users.models import User


class HiddifyPanel(models.Model):
    domain = models.TextField(null=False)
    panel_id = models.TextField(null=False)
    admin_id = models.TextField(null=False)

    def __str__(self):
        return self.domain


class Subscription(models.Model):
    class SubscriptionMode(models.TextChoices):
        NO_RESET = "no_reset"
        DAILY = "daily"
        WEEKLY = "weekly"
        MONTHLY = "monthly"

    package_days = models.PositiveBigIntegerField(null=False, default=90)
    usage_limit = models.PositiveBigIntegerField(null=False, default=50, help_text="In GB")
    mode = models.CharField(null=False, default=SubscriptionMode.NO_RESET, choices=SubscriptionMode.choices)
    hiddify = models.ForeignKey(HiddifyPanel, on_delete=models.CASCADE, null=False)


class VPN(models):
    link = models.TextField(null=False, blank=False)
    user_uuid = models.TextField(null=False, blank=False)
    user = models.ForeignKey(User, related_name="vpns", on_delete=models.CASCADE)
    active_days = models.PositiveBigIntegerField(default=90)
    payment = models.ForeignKey(Payment, related_name="vpn_links", null=False, on_delete=models.PROTECT)

    @property
    def left_days(self):
        return self.active_days - (datetime.date.today() - self.created_at.date()).days
