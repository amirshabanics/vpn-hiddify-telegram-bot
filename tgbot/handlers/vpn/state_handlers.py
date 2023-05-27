from users.models import User, Payment
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from users.utils import get_usdt_transaction_on_trc20_info
from tgbot.handlers.onboarding_start.static_text import (
    invalid_transaction_hash,
    payment_not_found,
    hash_used_before,
    payment_detected,
)
from tgbot.handlers.onboarding_start.keyboards import make_keyboard_for_get_trx_has


def get_trx_hash(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    trx_hash = update.message.text
    if Payment.objects.filter(trx_hash=trx_hash).exists():
        context.bot.send_message(
            text=hash_used_before,
            chat_id=u.user_id,
            reply_markup=make_keyboard_for_get_trx_has(),
        )
        return
    trx_info = get_usdt_transaction_on_trc20_info(trx_hash)
    if trx_info is None or not trx_info.is_success:
        context.bot.send_message(
            text=invalid_transaction_hash,
            chat_id=u.user_id,
            reply_markup=make_keyboard_for_get_trx_has(),
        )
        return
    payment_query = Payment.objects.filter(
        user=u,
        to_address=trx_info.to_address,
        amount__lte=trx_info.amount,
        status=Payment.PaymentStatus.IN_PROGRESS
    ).order_by("-amount", "-created_at")
    if not payment_query.exists():
        context.bot.send_message(
            text=payment_not_found,
            chat_id=u.user_id,
            reply_markup=make_keyboard_for_get_trx_has(),
        )
        return
    payment = payment_query.first()
    payment.trx_hash = trx_hash
    payment.status = Payment.PaymentStatus.PAYED
    payment.save()
    u.chat_state = User.ChatStateChoices.NONE
    u.save()
    context.bot.send_message(
        text=payment_detected,
        chat_id=u.user_id,
    )