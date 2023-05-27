import datetime

from django.utils import timezone
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.onboarding_start import static_text
from tgbot.handlers.utils.info import extract_user_data_from_update
from users.models import User, VPN
from users.utils import create_payment_for_user
from tgbot.handlers.onboarding_start.keyboards import make_keyboard_for_start_command
from tgbot.handlers.onboarding_start.state_handlers import get_trx_hash
from tgbot.handlers.onboarding_start.manage_data import QR_CODE_LINK
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
    # callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    u = User.get_user(update, context)
    user_id = u.user_id
    # text = static_text.unlock_secret_room.format(
    #     user_count=User.objects.count(),
    #     active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    # )
    payment = create_payment_for_user(u)
    with open(settings.BASE_DIR / settings.QR_CODE, 'rb') as qr_code:
        context.bot.send_photo(
            caption=payment.to_address,
            chat_id=user_id,
            photo=qr_code
        )
    context.bot.send_message(
        text=static_text.create_payment_text.format(amount=payment.amount),
        chat_id=user_id,
    )
    # context.bot.edit_message_text(
    #     text="you can buy",
    #     chat_id=user_id,
    #     message_id=update.callback_query.message.message_id,
    #     parse_mode=ParseMode.HTML,
    #
    # )


def command_edu(update: Update, context: CallbackContext) -> None:
    # callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    user_id = extract_user_data_from_update(update)['user_id']
    # text = static_text.unlock_secret_room.format(
    #     user_count=User.objects.count(),
    #     active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    # )

    context.bot.edit_message_text(
        text="edit for edu",
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )


def command_list(update: Update, context: CallbackContext) -> None:
    # callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    user = User.get_user(update, context)
    # text = static_text.unlock_secret_room.format(
    #     user_count=User.objects.count(),
    #     active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    # )

    active_links = []
    for v in user.vpn_links.all():
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


def command_history(update: Update, context: CallbackContext) -> None:
    # callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    user = User.get_user(update, context)
    # text = static_text.unlock_secret_room.format(
    #     user_count=User.objects.count(),
    #     active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    # )
    res_text = "id. amount | minute left | to address | status | transaction hash\n"
    row_text = "{id}. {amount} USDT | {minute} Minutes left | {address} | {status} | {trx_hash}\n"
    for p in user.payments.all():
        res_text += row_text.format(
            id=p.id,
            amount=p.amount,
            minute=int(p.expired_after),
            address=p.to_address,
            status=p.status,
            trx_hash=p.trx_hash
        )

    context.bot.send_message(
        text=res_text,
        chat_id=user.user_id,
        parse_mode=ParseMode.HTML
    )


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
