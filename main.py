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

try:
    bot.polling(none_stop=True, interval=0)
except Exception as e:
    logger.opt(exception=True).error(f'Unexpected error: {e}')
