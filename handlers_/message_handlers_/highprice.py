import telebot
from telebot.types import Message
from loguru import logger

from utils.handling import make_message
from bot_redis import redis_db

from loader import bot


def get_searching_commands(message: Message):
    """
    ""/highprice"  - получает команду и начинает отбирать отели от самой высокой цены
    :param message: Message
    :return: None
    """
    chat_id = message.chat.id
    redis_db.hset(chat_id, 'order', 'PRICE_HIGHEST_FIRST')
    logger.info('"highprice" command is called')
    logger.info(redis_db.hget(chat_id, 'order'))
    state = redis_db.hget(chat_id, 'state')
    logger.info(f"Current state: {state}")
    bot.send_message(chat_id, make_message(message, 'question_'))