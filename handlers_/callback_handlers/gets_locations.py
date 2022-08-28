from utils.handling import is_input_correct, internationalize, make_message
from loader import bot
from telebot.types import Message
from api.locations import make_locations_list

import telebot


def get_locations(msg: Message):
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
