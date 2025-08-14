"""Weather service for fetching and processing weather data."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

from .config import config
from .models import CurrentWeather, WeatherForecast, Location, ForecastDay, WeatherUpdateResult
from .logger import get_logger


class WeatherServiceError(Exception):
    """Base exception for weather service errors."""
    pass


class APIError(WeatherServiceError):
    """API-related errors."""
    pass


class ValidationError(WeatherServiceError):
    """Data validation errors."""
    pass


class WeatherService:
    """Main weather service for fetching weather data."""
    
    def __init__(self):
        self.logger = get_logger("service")
        self.session = self._create_session()
        self._rate_limiter = self._RateLimiter(requests_per_minute=100)
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    async def get_current_weather(self, location: str) -> CurrentWeather:
        """Get current weather for a location."""
        await self._rate_limiter.wait_if_needed()
        
        try:
            self.logger.info(f"Fetching current weather for {location}")
            
            params = {
                "key": config.weather_api_key,
                "q": location,
                "aqi": "yes"
            }
            
            response = self.session.get(
                config.weather_current_url,
                params=params,
                timeout=config.request_timeout_seconds
            )
            
            if response.status_code == 401:
                raise APIError("Invalid API key")
            elif response.status_code == 400:
                raise APIError(f"Invalid location: {location}")
            elif response.status_code == 429:
                raise APIError("API rate limit exceeded")
            elif response.status_code != 200:
                raise APIError(f"API error: {response.status_code} - {response.text}")
            
            data = response.json()
            return self._parse_current_weather(data)
            
        except requests.RequestException as e:
            self.logger.error(f"Network error fetching weather for {location}: {e}")
            raise APIError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for {location}: {e}")
            raise ValidationError(f"Invalid JSON response: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching weather for {location}: {e}")
            raise WeatherServiceError(f"Unexpected error: {e}")
    
    async def get_weather_forecast(self, location: str, days: int = 5) -> WeatherForecast:
        """Get weather forecast for a location."""
        await self._rate_limiter.wait_if_needed()
        
        try:
            self.logger.info(f"Fetching {days}-day forecast for {location}")
            
            params = {
                "key": config.weather_api_key,
                "q": location,
                "days": min(days, 10),  # API limit
                "aqi": "yes",
                "alerts": "yes"
            }
            
            response = self.session.get(
                config.weather_forecast_url,
                params=params,
                timeout=config.request_timeout_seconds
            )
            
            if response.status_code != 200:
                raise APIError(f"Forecast API error: {response.status_code} - {response.text}")
            
            data = response.json()
            return self._parse_weather_forecast(data)
            
        except requests.RequestException as e:
            self.logger.error(f"Network error fetching forecast for {location}: {e}")
            raise APIError(f"Network error: {e}")
        except Exception as e:
            self.logger.error(f"Error fetching forecast for {location}: {e}")
            raise WeatherServiceError(f"Forecast error: {e}")
    
    async def get_multiple_locations_weather(self, locations: List[str]) -> WeatherUpdateResult:
        """Get current weather for multiple locations."""
        start_time = time.time()
        successful_locations = []
        errors = {}
        weather_data = {}
        
        self.logger.info(f"Fetching weather for {len(locations)} locations")
        
        # Process locations with concurrency control
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def fetch_location_weather(location: str):
            async with semaphore:
                try:
                    weather = await self.get_current_weather(location)
                    successful_locations.append(location)
                    weather_data[location] = weather
                    return weather
                except Exception as e:
                    errors[location] = str(e)
                    self.logger.error(f"Failed to fetch weather for {location}: {e}")
                    return None
        
        # Execute all requests concurrently
        tasks = [fetch_location_weather(loc) for loc in locations]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        result = WeatherUpdateResult(
            success=len(successful_locations) > 0,
            locations_updated=successful_locations,
            errors=errors,
            total_locations=len(locations),
            duration_seconds=duration
        )
        
        self.logger.info(f"Weather update completed: {len(successful_locations)}/{len(locations)} successful in {duration:.2f}s")
        
        return result, weather_data
    
    def _parse_current_weather(self, data: Dict[str, Any]) -> CurrentWeather:
        """Parse current weather data from API response."""
        try:
            location_data = data["location"]
            current_data = data["current"]
            
            location = Location(
                name=location_data["name"],
                region=location_data.get("region"),
                country=location_data["country"],
                latitude=location_data["lat"],
                longitude=location_data["lon"],
                timezone_id=location_data.get("tz_id"),
                local_time=datetime.fromisoformat(location_data["localtime"].replace(" ", "T")) if "localtime" in location_data else None
            )
            
            return CurrentWeather(
                location=location,
                temperature_c=current_data["temp_c"],
                temperature_f=current_data["temp_f"],
                condition=current_data["condition"]["text"],
                condition_icon=current_data["condition"].get("icon"),
                humidity=current_data["humidity"],
                feels_like_c=current_data["feelslike_c"],
                feels_like_f=current_data["feelslike_f"],
                wind_speed_kph=current_data["wind_kph"],
                wind_speed_mph=current_data["wind_mph"],
                wind_direction=current_data["wind_dir"],
                wind_degree=current_data["wind_degree"],
                pressure_mb=current_data["pressure_mb"],
                pressure_in=current_data["pressure_in"],
                visibility_km=current_data["vis_km"],
                visibility_miles=current_data["vis_miles"],
                uv_index=current_data["uv"],
                last_updated=datetime.fromisoformat(current_data["last_updated"].replace(" ", "T")),
                data_source="weatherapi"
            )
            
        except KeyError as e:
            self.logger.error(f"Missing required field in weather data: {e}")
            raise ValidationError(f"Missing required field: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing weather data: {e}")
            raise ValidationError(f"Data parsing error: {e}")
    
    def _parse_weather_forecast(self, data: Dict[str, Any]) -> WeatherForecast:
        """Parse weather forecast data from API response."""
        try:
            current_weather = self._parse_current_weather(data)
            
            forecast_days = []
            for day_data in data["forecast"]["forecastday"]:
                day = day_data["day"]
                astro = day_data.get("astro", {})
                
                forecast_day = ForecastDay(
                    date=datetime.fromisoformat(day_data["date"]),
                    max_temp_c=day["maxtemp_c"],
                    max_temp_f=day["maxtemp_f"],
                    min_temp_c=day["mintemp_c"],
                    min_temp_f=day["mintemp_f"],
                    avg_temp_c=day["avgtemp_c"],
                    avg_temp_f=day["avgtemp_f"],
                    condition=day["condition"]["text"],
                    condition_icon=day["condition"].get("icon"),
                    chance_of_rain=day.get("daily_chance_of_rain", 0),
                    chance_of_snow=day.get("daily_chance_of_snow", 0),
                    max_wind_kph=day["maxwind_kph"],
                    max_wind_mph=day["maxwind_mph"],
                    total_precip_mm=day["totalprecip_mm"],
                    total_precip_in=day["totalprecip_in"],
                    avg_humidity=day["avghumidity"],
                    uv_index=day["uv"],
                    sunrise=astro.get("sunrise"),
                    sunset=astro.get("sunset"),
                    moonrise=astro.get("moonrise"),
                    moonset=astro.get("moonset"),
                    moon_phase=astro.get("moon_phase")
                )
                forecast_days.append(forecast_day)
            
            return WeatherForecast(
                location=current_weather.location,
                current=current_weather,
                forecast_days=forecast_days
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing forecast data: {e}")
            raise ValidationError(f"Forecast parsing error: {e}")
    
    class _RateLimiter:
        """Simple rate limiter for API requests."""
        
        def __init__(self, requests_per_minute: int):
            self.requests_per_minute = requests_per_minute
            self.requests = []
            self.lock = asyncio.Lock()
        
        async def wait_if_needed(self):
            async with self.lock:
                now = time.time()
                # Remove requests older than 1 minute
                self.requests = [req_time for req_time in self.requests if now - req_time < 60]
                
                if len(self.requests) >= self.requests_per_minute:
                    # Calculate how long to wait
                    oldest_request = min(self.requests)
                    wait_time = 60 - (now - oldest_request)
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                
                self.requests.append(now)


# Global weather service instance
weather_service = WeatherService()