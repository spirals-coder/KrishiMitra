import httpx
BASE='https://api.open-meteo.com/v1/forecast'
async def geocode(name: str):
    async with httpx.AsyncClient(timeout=10) as c:
        r=await c.get('https://geocoding-api.open-meteo.com/v1/search',params={'name':name,'count':5,'language':'en','format':'json'}); r.raise_for_status(); return r.json().get('results',[])
async def forecast(lat: float, lon: float):
    params={'latitude':lat,'longitude':lon,'current':'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m','daily':'temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum','forecast_days':7,'timezone':'auto'}
    async with httpx.AsyncClient(timeout=12) as c:
        r=await c.get(BASE,params=params); r.raise_for_status(); return r.json()
