import telebot
from telebot.types import Message, CallbackQuery
from loguru import logger

from handlers_.message_handlers_ import bestdeal_, highprice, lowprice

from api.hotels import get_hotels
from api.locations import exact_location, make_locations_list
from utils.handling import internationalize, is_input_correct, get_parameters_information, \
    make_message, steps, logger_config, is_user_in_db, add_user, extract_search_parameters
from bot_redis import redis_db

logger.configure(**logger_config)
BOT_TOKEN = '5550473457:AAEmMZsfZp5LTlzFQJvO4PiNvnc0aG1uD5Y'
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')


def get_locations(msg: Message) -> None:
    """
   берет имя места, собирает места с похожим именем и шлет в чат
    :param msg: Message
    :return: None
    """
    if not is_input_correct(msg):
        bot.send_message(msg.chat.id, make_message(msg, 'mistake_'))
    else:
        wait_msg = bot.send_message(msg.chat.id, internationalize('wait', msg))
        locations = make_locations_list(msg)
        bot.delete_message(msg.chat.id, wait_msg.id)
        if not locations or len(locations) < 1:
            bot.send_message(msg.chat.id, str(msg.text) + internationalize('locations_not_found', msg))
        elif locations.get('bad_request'):
            bot.send_message(msg.chat.id, internationalize('bad_request', msg))
        else:
            menu = telebot.types.InlineKeyboardMarkup()
            for loc_name, loc_id in locations.items():
                menu.add(telebot.types.InlineKeyboardButton(
                    text=loc_name,
                    callback_data='code' + loc_id)
                )
            menu.add(telebot.types.InlineKeyboardButton(text=internationalize('cancel', msg), callback_data='cancel'))
            bot.send_message(msg.chat.id, internationalize('loc_choose', msg), reply_markup=menu)


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
    if not is_user_in_db(message):
        add_user(message)
    if 'start' in message.text:
        logger.info(f'"start" command is called')
        bot.send_message(message.chat.id, internationalize('hello', message))
    else:
        logger.info(f'"help" command is called')
        bot.send_message(message.chat.id, internationalize('help', message))


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


def hotels_list(msg: Message) -> None:
    """
    присылает результаты поиска в чат
    :param msg: Message
    :return: None
    """
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


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    """
    обработка сообщений
    :param message: Message
    :return: None
    """
    if not is_user_in_db(message):
        add_user(message)
    state = redis_db.hget(message.chat.id, 'state')
    if state == '1':
        get_locations(message)
    elif state in ['2', '3', '4']:
        get_search_parameters(message)
    else:
        bot.send_message(message.chat.id, internationalize('misunderstanding', message))


try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    logger.opt(exception=True).error(f'Unexpected error: {e}')