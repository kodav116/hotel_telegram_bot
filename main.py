from telebot.types import Message, CallbackQuery
from loguru import logger

from handlers_.message_handlers_ import bestdeal_, highprice, lowprice, settings, help
from handlers_.callback_handlers import gets_locations

from keyboards.inline import buttons, get_message
from keyboards.reply import hotels_result, search_parameters

from utils.handling import logger_config, is_user_in_db, add_user
from bot_redis import redis_db
from loader import bot

logger.configure(**logger_config)


def get_locations(msg: Message) -> None:
    """
   берет имя места, собирает места с похожим именем и шлет в чат
    :param msg: Message
    :return: None
    """
    gets_locations.get_locations(msg)


@bot.message_handler(commands=['settings'])
def get_command_settings(message: Message) -> None:
    """
    "/settings" - открывает настройки
    :param message: Message
    :return: None
    """
    settings.get_command_settings(message)


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def get_searching_commands(message: Message) -> None:
    """
    "/lowprice", "/highprice", "/bestdeal"  - получает команду и начинает отбирать отели по параметру
    :param message: Message
    :return: None
    """
    logger.info("\n" + "=" * 100 + "\n")
    if not is_user_in_db(message):
        add_user(message)
    chat_id = message.chat.id
    redis_db.hset(chat_id, 'state', 1)
    if 'lowprice' in message.text:
        lowprice.get_searching_commands(message)
    elif 'highprice' in message.text:
        highprice.get_searching_commands(message)
    else:
        bestdeal_.get_searching_commands(message)


@bot.message_handler(commands=['help', 'start'])
def get_command_help(message: Message) -> None:
    """
    "/help" - присылает команды в чат
    :param message: Message
    :return: None
    """
    help.get_command_help(message)


@bot.callback_query_handler(func=lambda call: True)
def keyboard_handler(call: CallbackQuery) -> None:
    """
    делает кнопки
    :param call: CallbackQuery
    :return: None
    """
    buttons.keyboard_handler(call)


def get_search_parameters(msg: Message) -> None:
    """
    правит параметры поиска
    :param msg: Message
    :return: None
    """
    search_parameters.get_search_parameters(msg)


def hotels_list(msg: Message) -> None:
    """
    присылает результаты поиска в чат
    :param msg: Message
    :return: None
    """
    hotels_result.hotels_list(msg)


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    """
    обработка сообщений
    :param message: Message
    :return: None
    """
    get_message.get_text_messages(message)


try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    logger.opt(exception=True).error(f'Unexpected error: {e}')
