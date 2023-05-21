import datetime

from django.utils import timezone
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.onboarding_start import static_text
from tgbot.handlers.utils.info import extract_user_data_from_update
from users.models import User
from users.utils import create_payment_for_user
from tgbot.handlers.onboarding_start.keyboards import make_keyboard_for_start_command
from tgbot.handlers.onboarding_start.state_handlers import get_trx_hash
from tgbot.handlers.onboarding_start.manage_data import QR_CODE_LINK


def command_start(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    if u.chat_state == User.ChatStateChoices.GET_TRX_HASH.name:
        get_trx_hash(update, context)
        return

    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)
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
    create_payment_for_user(u)
    context.bot.send_photo(
        caption="send 10 usdt to this address in 10 min\nklsnsdlkvsd",
        chat_id=user_id,
        photo=QR_CODE_LINK
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
    user_id = extract_user_data_from_update(update)['user_id']
    # text = static_text.unlock_secret_room.format(
    #     user_count=User.objects.count(),
    #     active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    # )

    context.bot.edit_message_text(
        text="your links are",
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
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
