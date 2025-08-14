"""Data models for weather application."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class WeatherCondition(str, Enum):
    """Standard weather conditions."""
    CLEAR = "Clear"
    PARTLY_CLOUDY = "Partly cloudy"
    CLOUDY = "Cloudy"
    OVERCAST = "Overcast"
    RAIN = "Rain"
    HEAVY_RAIN = "Heavy rain"
    SNOW = "Snow"
    FOG = "Fog"
    THUNDERSTORM = "Thunderstorm"
    DRIZZLE = "Drizzle"
    UNKNOWN = "Unknown"


class Location(BaseModel):
    """Geographic location model."""
    name: str = Field(..., description="Location name")
    region: Optional[str] = Field(None, description="Region/state")
    country: str = Field(..., description="Country name")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    timezone_id: Optional[str] = Field(None, description="Timezone identifier")
    local_time: Optional[datetime] = Field(None, description="Local time")


class CurrentWeather(BaseModel):
    """Current weather data model."""
    location: Location = Field(..., description="Location information")
    temperature_c: float = Field(..., description="Temperature in Celsius")
    temperature_f: float = Field(..., description="Temperature in Fahrenheit")
    condition: str = Field(..., description="Weather condition")
    condition_icon: Optional[str] = Field(None, description="Weather condition icon URL")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    feels_like_c: float = Field(..., description="Feels like temperature in Celsius")
    feels_like_f: float = Field(..., description="Feels like temperature in Fahrenheit")
    wind_speed_kph: float = Field(..., description="Wind speed in km/h")
    wind_speed_mph: float = Field(..., description="Wind speed in mph")
    wind_direction: str = Field(..., description="Wind direction")
    wind_degree: int = Field(..., ge=0, le=360, description="Wind direction in degrees")
    pressure_mb: float = Field(..., description="Pressure in millibars")
    pressure_in: float = Field(..., description="Pressure in inches")
    visibility_km: float = Field(..., description="Visibility in kilometers")
    visibility_miles: float = Field(..., description="Visibility in miles")
    uv_index: float = Field(..., description="UV index")
    last_updated: datetime = Field(..., description="Last updated timestamp")
    data_source: str = Field(default="weatherapi", description="Data source identifier")


class ForecastDay(BaseModel):
    """Daily forecast model."""
    date: datetime = Field(..., description="Forecast date")
    max_temp_c: float = Field(..., description="Maximum temperature in Celsius")
    max_temp_f: float = Field(..., description="Maximum temperature in Fahrenheit")
    min_temp_c: float = Field(..., description="Minimum temperature in Celsius")
    min_temp_f: float = Field(..., description="Minimum temperature in Fahrenheit")
    avg_temp_c: float = Field(..., description="Average temperature in Celsius")
    avg_temp_f: float = Field(..., description="Average temperature in Fahrenheit")
    condition: str = Field(..., description="Weather condition")
    condition_icon: Optional[str] = Field(None, description="Weather condition icon URL")
    chance_of_rain: int = Field(..., ge=0, le=100, description="Chance of rain percentage")
    chance_of_snow: int = Field(..., ge=0, le=100, description="Chance of snow percentage")
    max_wind_kph: float = Field(..., description="Maximum wind speed in km/h")
    max_wind_mph: float = Field(..., description="Maximum wind speed in mph")
    total_precip_mm: float = Field(..., description="Total precipitation in mm")
    total_precip_in: float = Field(..., description="Total precipitation in inches")
    avg_humidity: int = Field(..., ge=0, le=100, description="Average humidity percentage")
    uv_index: float = Field(..., description="UV index")
    sunrise: Optional[str] = Field(None, description="Sunrise time")
    sunset: Optional[str] = Field(None, description="Sunset time")
    moonrise: Optional[str] = Field(None, description="Moonrise time")
    moonset: Optional[str] = Field(None, description="Moonset time")
    moon_phase: Optional[str] = Field(None, description="Moon phase")


class WeatherForecast(BaseModel):
    """Weather forecast model."""
    location: Location = Field(..., description="Location information")
    current: CurrentWeather = Field(..., description="Current weather")
    forecast_days: List[ForecastDay] = Field(..., description="Forecast days")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last updated timestamp")


class WeatherAlert(BaseModel):
    """Weather alert model."""
    id: Optional[str] = Field(None, description="Alert identifier")
    location: str = Field(..., description="Location name")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    start_time: datetime = Field(..., description="Alert start time")
    end_time: Optional[datetime] = Field(None, description="Alert end time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Alert creation time")
    is_active: bool = Field(default=True, description="Whether alert is active")


class WeatherThreshold(BaseModel):
    """Weather monitoring threshold model."""
    location: str = Field(..., description="Location name")
    metric: str = Field(..., description="Weather metric to monitor")
    min_value: Optional[float] = Field(None, description="Minimum threshold value")
    max_value: Optional[float] = Field(None, description="Maximum threshold value")
    alert_message: str = Field(..., description="Alert message template")
    is_enabled: bool = Field(default=True, description="Whether threshold monitoring is enabled")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Threshold creation time")


class WeatherUpdateResult(BaseModel):
    """Result of weather update operation."""
    success: bool = Field(..., description="Whether update was successful")
    locations_updated: List[str] = Field(default_factory=list, description="Successfully updated locations")
    errors: Dict[str, str] = Field(default_factory=dict, description="Errors by location")
    total_locations: int = Field(default=0, description="Total locations attempted")
    update_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")
    duration_seconds: float = Field(default=0.0, description="Update duration in seconds")


class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool = Field(..., description="Whether request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")