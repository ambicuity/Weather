"""Test configuration and weather service basic functionality."""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add src to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import WeatherConfig, config
from models import CurrentWeather, Location
from logger import get_logger


class TestConfig:
    """Test configuration management."""
    
    def test_config_default_values(self):
        """Test default configuration values."""
        test_config = WeatherConfig()
        
        assert test_config.log_level == "INFO"
        assert test_config.update_interval_minutes == 5
        assert test_config.cache_ttl_seconds == 300
        assert test_config.max_retries == 3
        assert test_config.request_timeout_seconds == 30
    
    def test_default_cities_property(self):
        """Test default cities parsing."""
        test_config = WeatherConfig()
        test_config.default_cities_str = "City1,City2, City3 ,City4"
        
        cities = test_config.default_cities
        assert len(cities) == 4
        assert "City1" in cities
        assert "City3" in cities  # Should be trimmed
        assert " City3 " not in cities
    
    def test_weather_api_urls(self):
        """Test weather API URL construction."""
        test_config = WeatherConfig()
        test_config.weather_api_base_url = "https://api.example.com/v1"
        
        assert test_config.weather_current_url == "https://api.example.com/v1/current.json"
        assert test_config.weather_forecast_url == "https://api.example.com/v1/forecast.json"


class TestModels:
    """Test data models."""
    
    def test_location_model(self):
        """Test Location model validation."""
        location = Location(
            name="Test City",
            country="Test Country",
            latitude=40.7128,
            longitude=-74.0060
        )
        
        assert location.name == "Test City"
        assert location.country == "Test Country"
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
    
    def test_current_weather_model(self):
        """Test CurrentWeather model validation."""
        location = Location(
            name="Test City",
            country="Test Country", 
            latitude=40.7128,
            longitude=-74.0060
        )
        
        from datetime import datetime
        
        weather = CurrentWeather(
            location=location,
            temperature_c=25.5,
            temperature_f=77.9,
            condition="Cloudy",
            humidity=65,
            feels_like_c=26.0,
            feels_like_f=78.8,
            wind_speed_kph=15.2,
            wind_speed_mph=9.4,
            wind_direction="NW",
            wind_degree=315,
            pressure_mb=1013.2,
            pressure_in=29.92,
            visibility_km=10.0,
            visibility_miles=6.2,
            uv_index=5.0,
            last_updated=datetime.utcnow()
        )
        
        assert weather.temperature_c == 25.5
        assert weather.humidity == 65
        assert weather.condition == "Cloudy"
        assert weather.location.name == "Test City"


class TestLogger:
    """Test logging functionality."""
    
    def test_logger_creation(self):
        """Test logger creation."""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "weather.test"
    
    def test_log_methods(self):
        """Test logging methods don't raise errors."""
        logger = get_logger("test")
        
        # These should not raise exceptions
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        logger.error("Test error message")


@pytest.mark.asyncio
class TestWeatherService:
    """Test weather service with mocked API calls."""
    
    async def test_weather_service_import(self):
        """Test weather service can be imported."""
        from weather_service import WeatherService
        service = WeatherService()
        assert service is not None
    
    @patch('weather_service.requests.Session.get')
    async def test_parse_current_weather(self, mock_get):
        """Test weather data parsing."""
        from weather_service import WeatherService
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "location": {
                "name": "Test City",
                "region": "Test Region",
                "country": "Test Country",
                "lat": 40.7128,
                "lon": -74.0060,
                "tz_id": "America/New_York",
                "localtime": "2023-01-01 12:00"
            },
            "current": {
                "temp_c": 25.5,
                "temp_f": 77.9,
                "condition": {"text": "Cloudy", "icon": "//example.com/icon.png"},
                "humidity": 65,
                "feelslike_c": 26.0,
                "feelslike_f": 78.8,
                "wind_kph": 15.2,
                "wind_mph": 9.4,
                "wind_dir": "NW",
                "wind_degree": 315,
                "pressure_mb": 1013.2,
                "pressure_in": 29.92,
                "vis_km": 10.0,
                "vis_miles": 6.2,
                "uv": 5.0,
                "last_updated": "2023-01-01 12:00"
            }
        }
        mock_get.return_value = mock_response
        
        service = WeatherService()
        weather = await service.get_current_weather("Test City")
        
        assert weather.location.name == "Test City"
        assert weather.temperature_c == 25.5
        assert weather.condition == "Cloudy"


if __name__ == "__main__":
    pytest.main([__file__])