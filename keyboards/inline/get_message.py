from utils.handling import is_user_in_db, add_user, internationalize
from bot_redis import redis_db

from handlers_.callback_handlers.gets_locations import get_locations
from keyboards.reply.search_parameters import get_search_parameters

from loader import bot


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