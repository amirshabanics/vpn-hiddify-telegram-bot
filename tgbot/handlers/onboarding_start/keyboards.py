from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.handlers.onboarding_start.manage_data import (
    BUY_BUTTON,
    EDU_BUTTON,
    LINK_LIST_BUTTON,
    CANCEL_BUTTON,
    HISTORY_BUTTON,
)
from tgbot.handlers.onboarding_start.static_text import (
    buy_button_text,
    my_links_button_text,
    education_button_text,
    cancel_get_trx_hash,
    my_trx_history_text,
)


def make_keyboard_for_start_command() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(buy_button_text, callback_data=f'{BUY_BUTTON}'),
            InlineKeyboardButton(my_links_button_text, callback_data=f'{LINK_LIST_BUTTON}'),
            InlineKeyboardButton(my_trx_history_text, callback_data=f'{HISTORY_BUTTON}')
        ],
        [
            InlineKeyboardButton(education_button_text, callback_data=f'{EDU_BUTTON}'),

        ]
    ]

    return InlineKeyboardMarkup(buttons)


def make_keyboard_for_get_trx_has() -> InlineKeyboardMarkup:
    buttons = [[
        InlineKeyboardButton(cancel_get_trx_hash, callback_data=f'{CANCEL_BUTTON}')
    ]]

    return InlineKeyboardMarkup(buttons)
