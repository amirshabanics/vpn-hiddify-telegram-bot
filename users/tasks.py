"""
    Celery tasks. Some of them will be launched periodically from admin panel via django-celery-beat
"""

import time
from typing import Union, List, Optional, Dict

import telegram

from dtb.celery import app
from celery.utils.log import get_task_logger
from tgbot.handlers.broadcast_message.utils import send_one_message, from_celery_entities_to_entities, \
    from_celery_markup_to_markup
from users.models import Payment
from users.utils import get_usdt_transaction_on_trc20_info, create_vpn_for_payment
from users.consts import *

logger = get_task_logger(__name__)


@app.task(ignore_result=True)
def update_payment_status():
    payments = Payment.objects.filter(status__in=[Payment.PaymentStatus.PAYED, Payment.PaymentStatus.IN_PROGRESS])
    for p in payments:

        if p.status == Payment.PaymentStatus.PAYED:
            trx_info = get_usdt_transaction_on_trc20_info(p.trx_hash)
            if trx_info.confirmed and trx_info.is_success:
                p.status = Payment.PaymentStatus.PAYED_AND_CONFIRMED
                p.save()
                vpn = create_vpn_for_payment(p)
                send_one_message(
                    text=CONFIRMED_PAYMENT,
                    user_id=p.user.user_id,
                )
            continue

        # 10 minutes
        if p.expired_after <= 0:
            p.status = Payment.PaymentStatus.FAILURE
            p.save()
            send_one_message(
                text=EXPIRED_PAYMENT,
                user_id=p.user.user_id,
            )


@app.task(ignore_result=True)
def broadcast_message(
        user_ids: List[Union[str, int]],
        text: str,
        entities: Optional[List[Dict]] = None,
        reply_markup: Optional[List[List[Dict]]] = None,
        sleep_between: float = 0.4,
        parse_mode=telegram.ParseMode.HTML,
) -> None:
    """ It's used to broadcast message to big amount of users """
    logger.info(f"Going to send message: '{text}' to {len(user_ids)} users")

    entities_ = from_celery_entities_to_entities(entities)
    reply_markup_ = from_celery_markup_to_markup(reply_markup)
    for user_id in user_ids:
        try:
            send_one_message(
                user_id=user_id,
                text=text,
                entities=entities_,
                parse_mode=parse_mode,
                reply_markup=reply_markup_,
            )
            logger.info(f"Broadcast message was sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}, reason: {e}")
        time.sleep(max(sleep_between, 0.1))

    logger.info("Broadcast finished!")
