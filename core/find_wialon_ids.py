import os
import django
import requests
import json

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

def find_units():
    print("--- Подключение к Wialon... ---")
    session = requests.Session()
    # Используем URL из settings или дефолтный
    base_url = getattr(settings, 'WIALON_BASE_URL', 'https://hst-api.wialon.com/wialon/ajax.html')
    token = getattr(settings, 'WIALON_TOKEN', '')

    if not token:
        print("ОШИБКА: Токен не найден в settings.py")
        return

    # 1. ЛОГИН
    try:
        login_resp = session.get(base_url, params={
            'svc': 'token/login',
            'params': json.dumps({"token": token})
        })
        login_data = login_resp.json()
        
        if 'eid' not in login_data:
            print("ОШИБКА АВТОРИЗАЦИИ:", login_data)
            return
            
        sid = login_data['eid']
    except Exception as e:
        print(f"Ошибка соединения: {e}")
        return

    # 2. ПОИСК
    search_params = {
        "spec": {
            "itemsType": "avl_unit",
            "propName": "sys_name",
            "propValueMask": "*",
            "sortType": "sys_name"
        },
        "force": 1,
        "flags": 1, # Флаг 1 возвращает базовые свойства, включая uid
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

        if 'items' in data:
            print("\n" + "="*85)
            print(f"{'ВНУТРЕННИЙ ID':<15} | {'UNIQUE ID (IMEI)':<20} | {'ИМЯ МАШИНЫ'}")
            print(f"{'(Вставлять в сайт)':<15} | {'(Из свойств)':<20} |")
            print("="*85)
            
            for item in data['items']:
                # internal_id - это то, что нужно вставить в Django
                internal_id = item['id']
                # unique_id - это то, что вы видите в свойствах (9175875064)
                unique_id = item.get('uid', 'нет')
                name = item['nm']
                
                print(f"{internal_id:<15} | {unique_id:<20} | {name}")
            print("="*85 + "\n")
        else:
            print("Машины не найдены.", data)

    except Exception as e:
        print(f"Ошибка поиска: {e}")

if __name__ == '__main__':
    find_units()