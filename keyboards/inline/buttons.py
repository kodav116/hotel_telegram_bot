from loguru import logger
from telebot.types import CallbackQuery
from loader import bot

from bot_redis import redis_db
from utils.handling import internationalize, make_message
from api.locations import exact_location

import telebot


@bot.callback_query_handler(func=lambda call: True)
def keyboard_handler(call: CallbackQuery) -> None:
    """
    делает кнопки
    :param call: CallbackQuery
    :return: None
    """
    logger.info(f'Function {keyboard_handler.__name__} called with argument: {call}')
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id)

    if call.data.startswith('code'):
        if redis_db.hget(chat_id, 'state') != '1':
            bot.send_message(call.message.chat.id, internationalize('enter_command', call.message))
            redis_db.hset(chat_id, 'state', 0)
        else:
            loc_name = exact_location(call.message.json, call.data)
            redis_db.hset(chat_id, mapping={"destination_id": call.data[4:]})
            logger.info(f"{loc_name} selected")
            bot.send_message(
                chat_id,
                f"{internationalize('loc_selected', call.message)}: {loc_name}",
            )
            if redis_db.hget(chat_id, 'order') == 'DISTANCE_FROM_LANDMARK':
                redis_db.hincrby(chat_id, 'state', 1)
            else:
                redis_db.hincrby(chat_id, 'state', 3)
            bot.send_message(chat_id, make_message(call.message, 'question_'))

    elif call.data.startswith('set'):
        redis_db.hset(chat_id, 'state', 0)
        menu = telebot.types.InlineKeyboardMarkup()
        if call.data == 'set_locale':
            logger.info(f'language change menu')
            menu.add(telebot.types.InlineKeyboardButton(text='Русский', callback_data='loc_ru_RU'))
            menu.add(telebot.types.InlineKeyboardButton(text='English', callback_data='loc_en_US'))
        elif call.data == 'set_currency':
            logger.info(f'currency change menu')
            menu.add(telebot.types.InlineKeyboardButton(text='RUB', callback_data='cur_RUB'))
            menu.add(telebot.types.InlineKeyboardButton(text='USD', callback_data='cur_USD'))
            menu.add(telebot.types.InlineKeyboardButton(text='EUR', callback_data='cur_EUR'))
        menu.add(telebot.types.InlineKeyboardButton(text=internationalize('cancel', call.message), callback_data='cancel'))
        bot.send_message(chat_id, internationalize('ask_to_select', call.message), reply_markup=menu)

    elif call.data.startswith('loc'):
        redis_db.hmset(chat_id, mapping={"locale": call.data[4:], "language": call.data[4:6]})
        bot.send_message(chat_id, f"{internationalize('current_language', call.message)}: {internationalize('language', call.message)}")
        logger.info(f"Language changed to {redis_db.hget(chat_id, 'language')}")
        logger.info(f"Locale changed to {redis_db.hget(chat_id, 'locale')}")

    elif call.data.startswith('cur'):
        redis_db.hset(chat_id, 'currency', call.data[4:])
        bot.send_message(chat_id, f"{internationalize('current_currency', call.message)}: {call.data[4:]}")
        logger.info(f"Currency changed to {redis_db.hget(chat_id, 'currency')}")

    elif call.data == 'cancel':
        logger.info(f'Canceled by user')
        redis_db.hset(chat_id, 'state', 0)
        bot.send_message(chat_id, internationalize('canceled', call.message))