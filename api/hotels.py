import requests

from loguru import logger
from telebot.types import Message

from utils.handling import check_in_n_out_dates, hotel_price, internationalize, hotel_address, \
    hotel_rating
from bot_redis import redis_db
from loader import X_RAPIDAPI_KEY


def get_hotels(msg: Message, parameters: dict) -> [list, None]:
    """
    Вызывает функции для обработки данных об отеле
    :param msg: Message
    :param parameters: search parameters
    :return: list with string like hotel descriptions
    """
    data = request_hotels(parameters)
    if 'bad_req' in data:
        return ['bad_request']
    data = structure_hotels_info(msg, data)
    if not data or len(data['results']) < 1:
        return None
    if parameters['order'] == 'DISTANCE_FROM_LANDMARK':
        next_page = data.get('next_page')
        distance = float(parameters['distance'])
        while next_page and next_page < 5 and float(data['results'][-1]['distance'].replace(',', '.').split()[0]) <= distance:
            add_data = request_hotels(parameters, next_page)
            if 'bad_req' in data:
                logger.warning('bad_request')
                break
            add_data = structure_hotels_info(msg, add_data)
            if add_data and len(add_data["results"]) > 0:
                data['results'].extend(add_data['results'])
                next_page = add_data['next_page']
            else:
                break
        quantity = int(parameters['quantity'])
        data = choose_best_hotels(data['results'], distance, quantity)
    else:
        data = data['results']

    data = generate_hotels_descriptions(data, msg)
    return data


def hotel_api_req(url: str, headers: dict, querystring: dict):
    try:
        response = requests.request("GET", url, headers=headers, params=querystring, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if data.get('message'):
                raise requests.exceptions.RequestException

            logger.info(f'Hotels api(properties/list) response received: {data}')
            return data

    except requests.exceptions.RequestException as e:
        logger.error(f'Error receiving response: {e}')
        return {'bad_req': 'bad_req'}
    except Exception as e:
        logger.info(f'Error in function {request_hotels.__name__}: {e}')
        return {'bad_req': 'bad_req'}


def request_hotels(parameters: dict, page: int = 1):
    """
    Запрашивает инфу об отеле с API
    :param parameters: search parameters
    :param page: page number
    :return: response from hotel api
    """
    logger.info(f'Function {request_hotels.__name__} called with argument: page = {page}, parameters = {parameters}')
    url = "https://hotels4.p.rapidapi.com/properties/list"
    dates = check_in_n_out_dates()

    querystring = {
        "adults1": "1",
        "pageNumber": page,
        "destinationId": parameters['destination_id'],
        "pageSize": parameters['quantity'],
        "checkOut": dates['check_out'],
        "checkIn": dates['check_in'],
        "sortOrder": parameters['order'],
        "locale": parameters['locale'],
        "currency": parameters['currency'],
    }
    headers = {
        'x-rapidapi-key': X_RAPIDAPI_KEY,
        'x-rapidapi-host': "hotels4.p.rapidapi.com"
    }
    if parameters['order'] == 'DISTANCE_FROM_LANDMARK':
        querystring['priceMax'] = parameters['max_price']
        querystring['priceMin'] = parameters['min_price']
        querystring['pageSize'] = '25'

    logger.info(f'Search parameters: {querystring}')

    data = hotel_api_req(url, headers, querystring)
    return data


def structure_hotels_info(msg: Message, data: dict) -> dict:
    """
    Сортирует инфу об отеле.
    :param msg: Message
    :param data: hotel data
    :return: dict of structured hotel data
    """
    logger.info(f'Function {structure_hotels_info.__name__} called with argument: msd = {msg}, data = {data}')
    data = data.get('data', {}).get('body', {}).get('searchResults')
    hotels = dict()
    hotels['total_count'] = data.get('totalCount', 0)

    logger.info(f"Next page: {data.get('pagination', {}).get('nextPageNumber', 0)}")
    hotels['next_page'] = data.get('pagination', {}).get('nextPageNumber')
    hotels['results'] = []

    try:
        if hotels['total_count'] > 0:
            for cur_hotel in data.get('results'):
                hotel = dict()
                hotel['name'] = cur_hotel.get('name')
                hotel['star_rating'] = cur_hotel.get('starRating', 0)
                hotel['price'] = hotel_price(cur_hotel)
                if not hotel['price']:
                    continue
                hotel['distance'] = cur_hotel.get('landmarks')[0].get('distance', internationalize('no_information', msg))
                hotel['address'] = hotel_address(cur_hotel, msg)

                if hotel not in hotels['results']:
                    hotels['results'].append(hotel)
        logger.info(f'Hotels in function {structure_hotels_info.__name__}: {hotels}')
        return hotels

    except Exception as e:
        logger.info(f'Error in function {structure_hotels_info.__name__}: {e}')


def choose_best_hotels(hotels: list[dict], distance: float, limit: int) -> list[dict]:
    """
    Удаляет отели, которые дальше определенного расстояния от центра города, сортирует остальные по цене и
    ограничивает выбор.
    :param limit: number of hotels
    :param distance: maximum distance from city center
    :param hotels: structured hotels data
    :return: required number of best hotels
    """
    logger.info(f'Function {choose_best_hotels.__name__} called with arguments: '
                f'distance = {distance}, quantity = {limit}\n{hotels}')
    hotels = list(filter(lambda x: float(x["distance"].strip().replace(',', '.').split()[0]) <= distance, hotels))
    logger.info(f'Hotels filtered: {hotels}')
    hotels = sorted(hotels, key=lambda k: k["price"])
    logger.info(f'Hotels sorted: {hotels}')
    if len(hotels) > limit:
        hotels = hotels[:limit]
    return hotels


def generate_hotels_descriptions(hotels: dict, msg: Message) -> list[str]:
    """
    Делает описание для отеля.
    :param msg: Message
    :param hotels: Hotels information
    :return: list with string like hotel descriptions
    """
    logger.info(f'Function {generate_hotels_descriptions.__name__} called with argument {hotels}')
    hotels_info = []

    for hotel in hotels:
        message = (
            f"{internationalize('hotel', msg)}: {hotel.get('name')}\n"
            f"{internationalize('rating', msg)}: {hotel_rating(hotel.get('star_rating'), msg)}\n"
            f"{internationalize('price', msg)}: {hotel['price']} {redis_db.hget(msg.chat.id, 'currency')}\n"
            f"{internationalize('distance', msg)}: {hotel.get('distance')}\n"
            f"{internationalize('address', msg)}: {hotel.get('address')}\n"
        )
        hotels_info.append(message)
    return hotels_info
