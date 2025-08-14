"""Configuration management for the Weather application."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv

load_dotenv()


class WeatherConfig(BaseSettings):
    """Weather application configuration."""
    
    # Weather API Configuration
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    weather_api_base_url: str = os.getenv("WEATHER_API_BASE_URL", "http://api.weatherapi.com/v1")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///weather.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Email Configuration
    email_smtp_host: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    email_smtp_port: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    email_username: str = os.getenv("EMAIL_USERNAME", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")
    notification_email_to: str = os.getenv("NOTIFICATION_EMAIL_TO", "")
    
    # Application Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    update_interval_minutes: int = int(os.getenv("UPDATE_INTERVAL_MINUTES", "5"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    
    # Cities Configuration
    default_cities_str: str = os.getenv("DEFAULT_CITIES", "Valsad,Boston,New York,London,Tokyo")
    
    @validator("weather_api_key")
    def validate_api_key(cls, v):
        if not v:
            raise ValueError("WEATHER_API_KEY is required")
        return v
    
    @property
    def default_cities(self) -> List[str]:
        """Get the default cities as a list."""
        return [city.strip() for city in self.default_cities_str.split(",") if city.strip()]
    
    @property
    def weather_current_url(self) -> str:
        """Get the current weather API URL."""
        return f"{self.weather_api_base_url}/current.json"
    
    @property
    def weather_forecast_url(self) -> str:
        """Get the forecast weather API URL."""
        return f"{self.weather_api_base_url}/forecast.json"
    
    class Config:
        case_sensitive = False


# Global configuration instance
config = WeatherConfig()