from __future__ import annotations

from typing import Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class User(CreateUpdateTracker):
    class ChatStateChoices(models.TextChoices):
        GET_TRX_HASH = "GET_TRX_HASH"
        NONE = "NONE"

    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)

    is_blocked_bot = models.BooleanField(default=False)

    is_admin = models.BooleanField(default=False)
    chat_state = models.CharField(
        max_length=64,
        default=ChatStateChoices.NONE,
        null=True,
        choices=ChatStateChoices.choices
    )

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    u.deep_link = payload
                    u.save()

        return u, created

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"


class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()

    objects = GetOrNoneManager()

    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"

#
# class Payment(CreateUpdateTracker):
#     class PaymentStatus(models.TextChoices):
#         # A cron job check whether time passed to pay the amount
#         FAILURE = "FAILURE"
#         IN_PROGRESS = "IN_PROGRESS"
#         PAYED = "PAYED"
#         PAYED_AND_CONFIRMED = "PAYED_AND_CONFIRMED"
#         SUCCESS = "SUCCESS"
#
#     user = models.ForeignKey(User, related_name="payments", on_delete=models.PROTECT)
#     amount = models.PositiveBigIntegerField(help_text="amount in usdt")
#     status = models.CharField(max_length=64, choices=PaymentStatus.choices, default=PaymentStatus.IN_PROGRESS)
#     to_address = models.TextField(null=False)
#     trx_hash = models.TextField()
#
#     @property
#     def expired_after(self):
#         expired = 10 - (datetime.datetime.now(tz=datetime.timezone.utc) - self.created_at).total_seconds() / 60
#
#         return expired if expired > 0 else 0

#
# class VPN(CreateTracker):
#     link = models.TextField(null=False, blank=False)
#     user = models.ForeignKey(User, related_name="vpn_links", on_delete=models.PROTECT)
#     active_days = models.PositiveBigIntegerField(default=90)
#     payment = models.ForeignKey(Payment, related_name="vpn_links", null=False, on_delete=models.PROTECT)
#
#     @property
#     def left_days(self):
#         return self.active_days - (datetime.date.today() - self.created_at.date()).days
