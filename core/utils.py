from django.core.cache import cache
import requests
from django.conf import settings

def get_weather(city):
    cache_key = f"weather_{city.lower()}"
    cached_weather = cache.get(cache_key)
    if cached_weather:
        return cached_weather

    API_KEY = settings.OPENWEATHER_API_KEY
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric',  # or 'imperial' for Fahrenheit
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        if response.status_code == 200:
            weather = {
                'description': data['weather'][0]['description'],
                'temperature': data['main']['temp'],
                'icon': data['weather'][0]['icon'],  # icon code for weather image
            }
            return weather
        else:
            return None
    except:
        return None