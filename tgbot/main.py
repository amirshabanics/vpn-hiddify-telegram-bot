import logging
import sys

import telegram
from telegram import Bot

from dtb.settings import TELEGRAM_TOKEN
from .system_commands import set_up_commands

bot = Bot(TELEGRAM_TOKEN)

TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
# Global variable - the best way I found to init Telegram bot
try:
    pass
except telegram.error.Unauthorized:
    logging.error("Invalid TELEGRAM_TOKEN.")
    sys.exit(1)
# todo for create command
# set_up_commands(bot)
