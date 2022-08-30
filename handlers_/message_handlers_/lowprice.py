from telebot.types import Message
from loguru import logger

from utils.handling import make_message, is_user_in_db, add_user
from bot_redis import redis_db
from loader import bot


@bot.message_handler(commands=['lowprice'])
def get_searching_commands(message: Message) -> None:
    """
    ""/lowprice"  - получает команду и начинает отбирать отели от самой низкой цены
    :param message: Message
    :return: None
    """
    logger.info("\n" + "=" * 100 + "\n")
    if not is_user_in_db(message):
        add_user(message)
    chat_id = message.chat.id
    redis_db.hset(chat_id, 'state', 1)
    chat_id = message.chat.id
    redis_db.hset(chat_id, 'order', 'PRICE')
    logger.info('"lowprice" command is called')
    logger.info(redis_db.hget(chat_id, 'order'))
    state = redis_db.hget(chat_id, 'state')
    logger.info(f"Current state: {state}")
    bot.send_message(chat_id, make_message(message, 'question_'))