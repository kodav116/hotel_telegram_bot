from telebot.types import Message
from utils.handling import is_user_in_db, add_user, internationalize

from loguru import logger
from loader import bot


def get_command_help(message: Message) -> None:
    """
    "/help" - присылает команды в чат
    :param message: Message
    :return: None
    """
    if not is_user_in_db(message):
        add_user(message)
    if 'start' in message.text:
        logger.info(f'"start" command is called')
        bot.send_message(message.chat.id, internationalize('hello', message))
    else:
        logger.info(f'"help" command is called')
        bot.send_message(message.chat.id, internationalize('help', message))