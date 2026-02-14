import httpx
import time
from typing import List, Optional, Any
from fastapi import HTTPException
from app.config import settings
from app.schemas import WeatherResponse, NewsArticle

class CacheService:
    def __init__(self, ttl_seconds: int = 600):
        self.cache = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())

# Global cache instance
cache_service = CacheService()

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    async def get_weather(self, city: str) -> WeatherResponse:
        cache_key = f"weather:{city.lower()}"
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return cached_data

        params = {
            "q": city,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric"
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                weather_data = WeatherResponse(
                    city=data["name"],
                    temperature=data["main"]["temp"],
                    humidity=data["main"]["humidity"],
                    description=data["weather"][0]["description"],
                    icon_url=f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
                )
                cache_service.set(cache_key, weather_data)
                return weather_data
            except httpx.HTTPStatusError as e:
                print(f"OpenWeatherMap Error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 404:
                    raise HTTPException(status_code=404, detail=f"Weather data not found for city: {city}")
                raise HTTPException(status_code=502, detail="Error fetching weather data")
            except Exception as e:
                print(f"OpenWeatherMap Unexpected Error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

class NewsService:
    BASE_URL = "https://newsapi.org/v2/everything"

    async def get_news(self, city: str) -> List[NewsArticle]:
        cache_key = f"news:{city.lower()}"
        cached_data = cache_service.get(cache_key)
        if cached_data:
            return cached_data

        params = {
            "q": city,
            "apiKey": settings.NEWS_API_KEY,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 5
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                articles = []
                for item in data.get("articles", []):
                    # Skip removed articles or invalid ones
                    if item.get("title") == "[Removed]":
                        continue
                        
                    articles.append(NewsArticle(
                        title=item.get("title", "No Title"),
                        source=item.get("source", {}).get("name", "Unknown"),
                        url=item.get("url"),
                        description=item.get("description")
                    ))
                cache_service.set(cache_key, articles)
                return articles
            except httpx.HTTPStatusError as e:
                print(f"NewsAPI Error: {e.response.status_code} - {e.response.text}")
                # NewsAPI handles errors differently, but 401/429 are common
                # Return empty list on error to not block the whole dashboard? 
                # Requirement says "Professional error handling", so ideally we should log and maybe return empty or raise.
                # Let's raise for now as per previous logic, but maybe we should allow partial failure involved.
                # Reverting to original logic for consistency but adding cache set.
                raise HTTPException(status_code=502, detail="Error fetching news data")
            except Exception as e:
                print(f"NewsAPI Unexpected Error: {e}")
                # Log the error in a real app
                return []
