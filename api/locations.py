import re

import requests
from telebot.types import Message
from loguru import logger
from loader import X_RAPIDAPI_KEY

from bot_redis import redis_db


def exact_location(data: dict, loc_id: str) -> str:
    """
    Получает ID места и получает о нем информацию.
    :param data: dict Message
    :param loc_id: location id
    :return: location name
    """
    for loc in data['reply_markup']['inline_keyboard']:
        if loc[0]['callback_data'] == loc_id:
            return loc[0]['text']


def delete_tags(html_text):
    """
    Удаляет спец. символы
    :param html_text: текст до замены
    :return: текст после замены
    """
    text = re.sub('<([^<>]*)>', '', html_text)
    return text


def location_api_req(url: str, headers: dict, querystring: dict):
    """
    Сам запрос на API сервер
    :param url: ссылка на сайт APi
    :param headers: хост и ключ API
    :param querystring: информация о месте
    :return: ответ сервера
    """
    try:
        response = requests.request("GET", url, headers=headers, params=querystring, timeout=20)
        if response.status_code == 200:
            data = response.json()
            logger.info(f'Hotels api(locations) response received: {data}')

            if data.get('message'):
                logger.error(f'Problems with subscription to hotels api {data}')
                raise requests.exceptions.RequestException
            return data
    except requests.exceptions.RequestException as e:
        logger.error(f'Server error: {e}')
    except Exception as e:
        logger.error(f'Error: {e}')


def request_locations(msg):
    """
    Запрашивает инфу об отеле с API и возвращает её
    :param msg: Message
    :return: информация с API о месте
    """
    url = "https://hotels4.p.rapidapi.com/locations/search"
    querystring = {
        "query": msg.text.strip(),
        "locale": redis_db.hget(msg.chat.id, 'locale'),
    }
    headers = {
        'x-rapidapi-key': X_RAPIDAPI_KEY,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"
    }
    logger.info(f'Parameters for search locations: {querystring}')
    data = location_api_req(url, headers, querystring)
    return data


def make_locations_list(msg: Message) -> dict:
    """
   Получает информацию с API про отели и делает dict: location name - location id (место и id места)
    :param msg: Message
    :return: dict: location name - location id (место и id места)
    """
    data = request_locations(msg)
    if not data:
        return {'bad_request': 'bad_request'}

    try:
        locations = dict()
        if len(data.get('suggestions')[0].get('entities')) > 0:
            for item in data.get('suggestions')[0].get('entities'):
                location_name = delete_tags(item['caption'])
                locations[location_name] = item['destinationId']
            logger.info(locations)
            return locations
    except Exception as e:
        logger.error(f'Could not parse hotel api response. {e}')