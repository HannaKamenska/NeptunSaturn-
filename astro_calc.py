import swisseph as swe
import pytz
from geopy.geocoders import Nominatim
from datetime import datetime
import json
import os
from astro_utils import (
    calculate_planet_positions,
    calculate_houses,
    calculate_aspects,
    get_zodiac_sign,
    get_house_number
)

# Настройка эфемерид
swe.set_ephe_path('.')

def get_coordinates(city):
    geolocator = Nominatim(user_agent="astro_bot")
    location = geolocator.geocode(city)
    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError("Город не найден.")

def convert_to_utc(date_str, time_str, city):
    local = pytz.timezone("Europe/Moscow")  # В будущем: определять по городу
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    local_dt = local.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt

def save_user_data(user_data, user_id):
    os.makedirs("data", exist_ok=True)  # 🆕 создаём папку, если её нет
    filename = f"data/astro_user_{user_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=4, ensure_ascii=False)

def process_user_data(telegram_id, username, date_str, time_str, city):
    try:
        lat, lon = get_coordinates(city)
        utc_dt = convert_to_utc(date_str, time_str, city)
        jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute / 60)

        planets = calculate_planet_positions(jd)
        houses = calculate_houses(jd, lat, lon)
        aspects = calculate_aspects(planets, houses)

        for name, degree in planets.items():
            house = get_house_number(degree, houses["Houses"])
            planets[name] = {
                "degree": degree,
                "house": house
            }

        user_data = {
            "telegram_id": telegram_id,
            "username": username,
            "birth_date": date_str,
            "birth_time": time_str,
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "utc_time": utc_dt.isoformat(),
            "planets": planets,
            "houses": houses,
            "aspects": aspects
        }

        save_user_data(user_data, telegram_id)

        print("✅ Данные пользователя сохранены успешно!")

        return f"data/astro_user_{telegram_id}.json"

    except Exception as e:
        print(f"🚫 Ошибка: {e}")
        return None

# Для отладки вручную
if __name__ == "__main__":
    process_user_data(
        telegram_id=123456789,
        username="Anna",
        date_str="13.12.1986",
        time_str="14:56",
        city="Бердянск"
    )
