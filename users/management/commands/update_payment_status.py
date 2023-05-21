from django.core.management.base import BaseCommand
from users.models import Payment, User
from users.utils import get_usdt_transaction_on_trc20_info
from tgbot.main import bot
from datetime import datetime

EXPIRED_PAYMENT = "Your payment with id={id} expired."
CONFIRMED_PAYMENT = "Yupi! Your payment with id={id} confirmed. Please wait to create your vpn link."


class UpdatePaymentStatus(BaseCommand):
    payments = Payment.objects.filter(status=Payment.PaymentStatus.PAYED)
    for p in payments:
        # 10 minutes
        if (datetime.now() - p.created_at).total_seconds() > 10:
            bot.send_message(
                text=EXPIRED_PAYMENT.format(id=p.id),
                chat_id=p.user.user_id,
            )
            continue
        trx_info = get_usdt_transaction_on_trc20_info(p.trx_hash)
        if trx_info.confirmed and trx_info.is_success:
            p.status = Payment.PaymentStatus.PAYED_AND_CONFIRMED
            p.save()
            bot.send_message(
                text=CONFIRMED_PAYMENT.format(id=p.id),
                chat_id=p.user.user_id,
            )
