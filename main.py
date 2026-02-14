import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.schemas import DashboardResponse
from app.services import WeatherService, NewsService

app = FastAPI(title="Global Weather & News Dashboard")

weather_service = WeatherService()
news_service = NewsService()

@app.get("/dashboard/{city}", response_model=DashboardResponse)
async def get_dashboard(city: str):
    try:
        # Fetch weather and news concurrently
        weather_task = weather_service.get_weather(city)
        news_task = news_service.get_news(city)
        
        weather_data, news_data = await asyncio.gather(weather_task, news_task)
        
        return DashboardResponse(
            city=city.title(),
            weather=weather_data,
            news=news_data
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        # In case of unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please contact support."},
    )

@app.get("/")
async def root():
    return {"message": "Welcome to the Global Weather & News Dashboard API"}
