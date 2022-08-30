from utils.handling import is_user_in_db, add_user, internationalize
from loguru import logger
from loader import bot
from telebot.types import Message

import telebot


@bot.message_handler(commands=['settings'])
def get_command_settings(message: Message) -> None:
    """
    "/settings" - открывает настройки
    :param message: Message
    :return: None
    """
    if not is_user_in_db(message):
        add_user(message)
    logger.info(f'Функция {get_command_settings.__name__} вызвана с параметром: {message}')
    menu = telebot.types.InlineKeyboardMarkup()
    menu.add(telebot.types.InlineKeyboardButton(text=internationalize("language_", message), callback_data='set_locale'))
    menu.add(telebot.types.InlineKeyboardButton(text=internationalize("currency_", message), callback_data='set_currency'))
    menu.add(telebot.types.InlineKeyboardButton(text=internationalize("cancel", message), callback_data='cancel'))
    bot.send_message(message.chat.id, internationalize("settings", message), reply_markup=menu)