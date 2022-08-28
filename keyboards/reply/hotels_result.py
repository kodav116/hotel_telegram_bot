from loader import bot
from loguru import logger
from api.hotels import get_hotels

from utils.handling import internationalize, extract_search_parameters, get_parameters_information

from telebot.types import Message


def hotels_list(msg: Message) -> None:
    chat_id = msg.chat.id
    wait_msg = bot.send_message(chat_id, internationalize('wait', msg))
    params = extract_search_parameters(msg)
    hotels = get_hotels(msg, params)
    logger.info(f'Function {get_hotels.__name__} returned: {hotels}')
    bot.delete_message(chat_id, wait_msg.id)
    if not hotels or len(hotels) < 1:
        bot.send_message(chat_id, internationalize('hotels_not_found', msg))
    elif 'bad_request' in hotels:
        bot.send_message(chat_id, internationalize('bad_request', msg))
    else:
        quantity = len(hotels)
        bot.send_message(chat_id, get_parameters_information(msg))
        bot.send_message(chat_id, f"{internationalize('hotels_found', msg)}: {quantity}")
        for hotel in hotels:
            bot.send_message(chat_id, hotel)
