from users.models import User
from payment.models import DepositTransaction
from telegram import Update
from telegram.ext import CallbackContext
from payment.utils import get_usdt_transaction_on_trc20_info, can_transaction_be_confirmed
from tgbot.handlers.vpn.static_text import (
    invalid_transaction_hash,
    hash_used_before,
    payment_detected,
)
from tgbot.handlers.vpn.keyboards import make_keyboard_for_get_trx_has
from django.conf import settings


def get_trx_hash(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    trx_hash = update.message.text
    if DepositTransaction.objects.filter(trx_hash=trx_hash).exists():
        context.bot.send_message(
            text=hash_used_before,
            chat_id=u.user_id,
            reply_markup=make_keyboard_for_get_trx_has(),
        )
        return
    trx_info = get_usdt_transaction_on_trc20_info(trx_hash)
    if not can_transaction_be_confirmed(trx_info):
        context.bot.send_message(
            text=invalid_transaction_hash,
            chat_id=u.user_id,
            reply_markup=make_keyboard_for_get_trx_has(),
        )
        return

    DepositTransaction.objects.create(amount=trx_info.amount, to_address=trx_info.to_address, trx_hash=trx_hash, user=u)
    u.chat_state = User.ChatStateChoices.NONE
    u.save()
    context.bot.send_message(
        text=payment_detected,
        chat_id=u.user_id,
    )
