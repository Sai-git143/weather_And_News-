from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    humidity: int
    description: str
    icon_url: Optional[str] = None

class NewsArticle(BaseModel):
    title: str
    source: str
    url: HttpUrl
    description: Optional[str] = None

class DashboardResponse(BaseModel):
    city: str
    weather: WeatherResponse
    news: List[NewsArticle]
