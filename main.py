import telebot


bot = telebot.TeleBot('5550473457:AAEmMZsfZp5LTlzFQJvO4PiNvnc0aG1uD5Y')


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    """
    Получает на вход сообщения и выдает строку в ответ
    :param message:
    :return: None
    """
    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "Напиши 'Привет' или /hello_world.")
    elif message.text == '/hello_world':
        bot.send_message(message.from_user.id, "Привет, дивный новый мир!")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


bot.polling(none_stop=True, interval=0)