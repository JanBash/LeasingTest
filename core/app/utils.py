import requests
import json
from django.conf import settings

from bs4 import BeautifulSoup
import re

def get_wialon_location(wialon_unit_id):
    """
    Возвращает словарь {lat: float, lon: float} или None, если ошибка.
    """
    if not wialon_unit_id:
        return None

    session = requests.Session()
    # Если вы используете Wialon Local, адрес может отличаться
    base_url = getattr(settings, 'WIALON_BASE_URL', 'https://hst-api.wialon.com/wialon/ajax.html')
    token = getattr(settings, 'WIALON_TOKEN', '')

    if not token:
        print("Ошибка: Не задан WIALON_TOKEN в settings.py")
        return None

    # ---------------------------------------------------------
    # 1. ЛОГИН (Получаем sid)
    # ---------------------------------------------------------
    login_params = {
        "token": token
    }
    
    try:
        # ВНИМАНИЕ: Используем переменную login_resp, а не login
        login_resp = session.get(base_url, params={
            'svc': 'token/login',
            'params': json.dumps(login_params)
        })
        
        # Преобразуем ответ в JSON
        login_data = login_resp.json()
        
        # Проверяем, есть ли eid (это и есть sid сессии)
        if 'eid' not in login_data:
            print("Wialon Login Error:", login_data)
            return None
            
        sid = login_data['eid']
        
    except Exception as e:
        print(f"Connection Error (Login step): {e}")
        return None

    # ---------------------------------------------------------
    # 2. ПОЛУЧЕНИЕ КООРДИНАТ
    # ---------------------------------------------------------
    # flags=1024 (0x400) - это флаг "Последнее сообщение" (где лежат координаты)
    search_params = {
        "id": int(wialon_unit_id),
        "flags": 1024 
    }
    
    try:
        item_resp = session.get(base_url, params={
            'svc': 'core/search_item',
            'params': json.dumps(search_params),
            'sid': sid
        })
        item_data = item_resp.json()
        
        # Разбираем ответ. Координаты лежат в 'lmsg' (last message) -> 'pos'
        # Проверяем всю цепочку, чтобы не получить ошибку
        if ('item' in item_data and 
            item_data['item'] and 
            'lmsg' in item_data['item'] and 
            'pos' in item_data['item']['lmsg']):
            
            pos = item_data['item']['lmsg']['pos']
            
            return {
                'lat': pos['y'], # Y - широта
                'lon': pos['x']  # X - долгота
            }
        else:
            print(f"Данные о локации не найдены для ID {wialon_unit_id}. Ответ Wialon:", item_data)
            return None
        
    except Exception as e:
        print(f"Wialon Search Error: {e}")
        return None


def find_wialon_id_by_imei(imei):
    """
    Ищет внутренний ID объекта в Wialon по его IMEI (Unique ID).
    """
    if not imei:
        return None

    session = requests.Session()
    base_url = getattr(settings, 'WIALON_BASE_URL', 'https://hst-api.wialon.com/wialon/ajax.html')
    token = getattr(settings, 'WIALON_TOKEN', '')

    # 1. ЛОГИН
    try:
        login_resp = session.get(base_url, params={
            'svc': 'token/login',
            'params': json.dumps({"token": token})
        })
        login_data = login_resp.json()
        if 'eid' not in login_data:
            return None
        sid = login_data['eid']
    except:
        return None

    # 2. ПОИСК ПО IMEI (sys_unique_id)
    search_params = {
        "spec": {
            "itemsType": "avl_unit",
            "propName": "sys_unique_id", # Ищем именно по полю Unique ID
            "propValueMask": str(imei),  # Значение маски - ваш IMEI
            "sortType": "sys_name"
        },
        "force": 1,
        "flags": 1,
        "from": 0,
        "to": 0
    }

    try:
        resp = session.get(base_url, params={
            'svc': 'core/search_items',
            'params': json.dumps(search_params),
            'sid': sid
        })
        data = resp.json()

        # Если нашли хотя бы одну машину
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['id'] # Возвращаем внутренний ID первой найденной машины
    except:
        pass

    return None


def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Ошибка запроса {url}: {e}")
    return None


def clean_text(text):
    if text:
        return re.sub(r'\s+', ' ', text).strip()
    return '-'


def parse_mashina_kg(url):
    html = get_html(url)
    if not html: return None

    soup = BeautifulSoup(html, 'html.parser')
    data = {'source': 'Mashina.kg', 'url': url}

    try:
        # 1. Название
        h1 = soup.find('h1')
        data['title'] = clean_text(h1.text) if h1 else 'Без названия'

        # 2. Цена
        price_div = soup.find('div', class_='price-dollar')
        data['price'] = clean_text(price_div.text) if price_div else 'Не указана'


        img_tag = soup.select_one('.main-image img')
        if not img_tag:

            img_tag = soup.select_one('.image-gallery img')

        data['image'] = img_tag['src'] if img_tag else None

        full_text = soup.get_text()

        # Ищем год
        year_match = re.search(r'Год выпуска\s*(\d{4})', full_text)
        data['year'] = year_match.group(1) if year_match else '-'

        # Ищем пробег
        mileage_match = re.search(r'Пробег\s*(\d[\d\s]*)\s*км', full_text)
        data['mileage'] = mileage_match.group(1).replace(' ', '') + ' км' if mileage_match else '-'

        # Двигатель
        engine_match = re.search(r'Двигатель\s*(\d+(?:\.\d+)?)', full_text)
        fuel_match = re.search(r'(бензин|дизель|гибрид|электро)', full_text, re.IGNORECASE)
        data['engine'] = f"{engine_match.group(1) if engine_match else ''} {fuel_match.group(1) if fuel_match else ''}"

        # Коробка
        trans_match = re.search(r'Коробка\s*([а-яА-Яa-zA-Z]+)', full_text)
        data['transmission'] = trans_match.group(1) if trans_match else '-'

    except Exception as e:
        print(f"Ошибка парсинга Mashina.kg: {e}")

    return data


def parse_lalafo_kg(url):
    html = get_html(url)
    if not html: return None

    soup = BeautifulSoup(html, 'html.parser')
    data = {'source': 'Lalafo.kg', 'url': url}

    try:

        og_title = soup.find('meta', property='og:title')
        data['title'] = og_title['content'] if og_title else 'Lalafo объявление'

        og_image = soup.find('meta', property='og:image')
        data['image'] = og_image['content'] if og_image else None

        og_price = soup.find('meta', property='product:price:amount')
        og_currency = soup.find('meta', property='product:price:currency')
        if og_price:
            data['price'] = f"{og_price['content']} {og_currency['content'] if og_currency else ''}"
        else:

            price_tag = soup.find('span', class_='heading__price')
            data['price'] = clean_text(price_tag.text) if price_tag else 'Договорная'


        full_text = clean_text(soup.get_text())

        # Год
        year_match = re.search(r'Год выпуска:\s*(\d{4})', full_text)
        if not year_match:
            year_match = re.search(r'Год:\s*(\d{4})', full_text)
        data['year'] = year_match.group(1) if year_match else '-'

        # Пробег
        mileage_match = re.search(r'Пробег[^:]*:\s*(\d[\d\s]*)', full_text)
        data['mileage'] = mileage_match.group(1) + ' км' if mileage_match else '-'

        # Двигатель (Объем)
        vol_match = re.search(r'Объем двигателя:\s*(\d\.\d)', full_text)
        data['engine'] = vol_match.group(1) if vol_match else '-'

        # Коробка
        trans_match = re.search(r'Коробка передач:\s*([а-яА-Яa-zA-Z]+)', full_text)
        data['transmission'] = trans_match.group(1) if trans_match else '-'

    except Exception as e:
        print(f"Ошибка парсинга Lalafo: {e}")

    return data


def parse_external_url(url):
    if 'mashina.kg' in url:
        return parse_mashina_kg(url)
    elif 'lalafo' in url:
        return parse_lalafo_kg(url)
    return None
