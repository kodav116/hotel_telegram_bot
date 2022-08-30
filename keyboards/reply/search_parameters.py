from telebot.types import Message
from loguru import logger
from loader import bot
from keyboards.reply.hotels_result import hotels_list

from utils.handling import make_message, steps, is_input_correct
from handlers_.message_handlers_.settings import get_command_settings

from bot_redis import redis_db


def get_search_parameters(msg: Message) -> None:
    """
    правит параметры поиска
    :param msg: Message
    :return: None
    """
    logger.info(f'Function {get_command_settings.__name__} called with argument: {msg}')
    chat_id = msg.chat.id
    state = redis_db.hget(chat_id, 'state')
    if not is_input_correct(msg):
        bot.send_message(chat_id, make_message(msg, 'mistake_'))
    else:
        redis_db.hincrby(msg.chat.id, 'state', 1)
        if state == '2':
            min_price, max_price = sorted(msg.text.strip().split(), key=int)
            redis_db.hset(chat_id, steps[state + 'min'], min_price)
            logger.info(f"{steps[state + 'min']} set to {min_price}")
            redis_db.hset(chat_id, steps[state + 'max'], max_price)
            logger.info(f"{steps[state + 'max']} set to {max_price}")
            bot.send_message(chat_id, make_message(msg, 'question_'))
        elif state == '4':
            redis_db.hset(chat_id, steps[state], msg.text.strip())
            logger.info(f"{steps[state]} set to {msg.text.strip()}")
            redis_db.hset(chat_id, 'state', 0)
            hotels_list(msg)
        else:
            redis_db.hset(chat_id, steps[state], msg.text.strip())
            logger.info(f"{steps[state]} set to {msg.text.strip()}")
            bot.send_message(chat_id, make_message(msg, 'question_'))