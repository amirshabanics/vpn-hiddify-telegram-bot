from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.vpn import static_text
from tgbot.handlers.utils.info import extract_user_data_from_update
from users.models import User
from payment.utils import create_payment_for_user
from tgbot.handlers.vpn.keyboards import make_keyboard_for_start_command
from tgbot.handlers.vpn.state_handlers import get_trx_hash
from django.conf import settings


def command_start(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    if u.chat_state == User.ChatStateChoices.GET_TRX_HASH.name:
        get_trx_hash(update, context)
        return

    text = static_text.start_text.format(first_name=u.first_name)
    update.message.reply_text(text=text,
                              reply_markup=make_keyboard_for_start_command())


def command_buy(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    user_id = u.user_id
    payment, vpn, amount = create_payment_for_user(u)
    if amount == 0:
        context.bot.send_message(
            chat_id=user_id,
            text=static_text.wallet_has_enough_money,
        )
        return
    with open(settings.BASE_DIR / settings.QR_CODE, 'rb') as qr_code:
        context.bot.send_photo(
            caption=settings.WALLET,
            chat_id=user_id,
            photo=qr_code
        )
    context.bot.send_message(
        text=static_text.create_payment_text.format(
            amount=amount,
            days=vpn.subscription.package_days,
            usage=vpn.subscription.usage_limit
        ),
        chat_id=user_id,
    )


def command_edu(update: Update, context: CallbackContext) -> None:
    user_id = extract_user_data_from_update(update)['user_id']
    context.bot.edit_message_text(
        text="edit for edu",
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )


def command_list(update: Update, context: CallbackContext) -> None:
    user = User.get_user(update, context)
    active_links = []
    for v in user.vpns.all():
        if v.left_days > 0:
            active_links.append(v)

    res_text = ""
    row_text = "{index}. <a href='{link}'>Link</a> | {days:02d} days\n"
    for index, v in enumerate(active_links):
        res_text += row_text.format(index=index + 1, link=v.link, days=v.left_days)
    context.bot.send_message(
        text=res_text if len(res_text) > 0 else static_text.empty_vpn_link,
        chat_id=user.user_id,
        parse_mode=ParseMode.HTML
    )


# def command_history(update: Update, context: CallbackContext) -> None:
#     user = User.get_user(update, context)
#     res_text = "id. amount | minute left | to address | status | transaction hash\n"
#     row_text = "{id}. {amount} USDT | {minute} Minutes left | {address} | {status} | {trx_hash}\n"
#     for p in user.payments.all():
#         res_text += row_text.format(
#             id=p.id,
#             amount=p.amount,
#             minute=int(p.expired_after),
#             address=p.to_address,
#             status=p.status,
#             trx_hash=p.trx_hash
#         )
#
#     context.bot.send_message(
#         text=res_text,
#         chat_id=user.user_id,
#         parse_mode=ParseMode.HTML
#     )


def command_cancel(update: Update, context: CallbackContext) -> None:
    user = User.get_user(update, context)
    user.chat_state = User.ChatStateChoices.NONE
    user.save()

    context.bot.edit_message_text(
        text="Cancel successfully",
        chat_id=user.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )
