"""Weather forecast service with advanced prediction capabilities."""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
import statistics

from .config import config
from .weather_service import weather_service
from .database import weather_db
from .models import WeatherForecast, CurrentWeather, ForecastDay, WeatherAlert
from .logger import get_logger


class ForecastService:
    """Advanced weather forecasting service."""
    
    def __init__(self):
        self.logger = get_logger("forecast")
        self._prediction_models = {
            "simple": self._simple_trend_prediction,
            "moving_average": self._moving_average_prediction,
            "weighted": self._weighted_prediction
        }
    
    async def get_extended_forecast(self, location: str, days: int = 10) -> Dict[str, Any]:
        """Get extended forecast with multiple prediction models."""
        try:
            # Get official forecast
            official_forecast = await weather_service.get_weather_forecast(location, min(days, 10))
            
            # Get historical data for trend analysis
            historical_data = await weather_db.get_current_weather_history(location, hours=24*7)  # 7 days
            
            # If we need more days than official provides, use predictions
            extended_days = []
            if days > len(official_forecast.forecast_days):
                historical_trends = self._analyze_historical_trends(historical_data)
                
                # Generate additional predictions
                last_official_day = official_forecast.forecast_days[-1] if official_forecast.forecast_days else None
                
                for i in range(len(official_forecast.forecast_days), days):
                    predicted_day = await self._predict_weather_day(
                        location, 
                        last_official_day,
                        historical_trends,
                        days_ahead=i+1
                    )
                    extended_days.append(predicted_day)
            
            return {
                "location": official_forecast.location.dict(),
                "current": official_forecast.current.dict(),
                "official_forecast": [day.dict() for day in official_forecast.forecast_days],
                "extended_forecast": [day.dict() for day in extended_days],
                "total_days": len(official_forecast.forecast_days) + len(extended_days),
                "prediction_confidence": self._calculate_confidence(historical_data),
                "historical_trends": self._analyze_historical_trends(historical_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting extended forecast for {location}: {e}")
            raise
    
    async def get_hourly_forecast(self, location: str, hours: int = 24) -> Dict[str, Any]:
        """Get detailed hourly forecast (where available from API)."""
        try:
            # Get detailed forecast data
            forecast = await weather_service.get_weather_forecast(location, days=min(hours//24 + 1, 10))
            
            # For now, return daily data broken into hourly segments
            # In a real implementation, you'd use an API that provides hourly data
            hourly_data = []
            
            for day in forecast.forecast_days[:hours//24 + 1]:
                # Simulate hourly breakdown from daily data
                for hour in range(24):
                    if len(hourly_data) >= hours:
                        break
                    
                    hourly_temp = self._interpolate_hourly_temperature(
                        day.min_temp_c, day.max_temp_c, hour
                    )
                    
                    hourly_data.append({
                        "datetime": (day.date + timedelta(hours=hour)).isoformat(),
                        "temperature_c": round(hourly_temp, 1),
                        "condition": day.condition,
                        "humidity": day.avg_humidity,
                        "wind_kph": day.max_wind_kph * (0.7 + 0.3 * abs(12 - hour) / 12),  # Wind varies by time
                        "precipitation_chance": day.chance_of_rain,
                        "is_predicted": False  # This would be True for predicted hours
                    })
            
            return {
                "location": forecast.location.dict(),
                "hourly_forecast": hourly_data[:hours],
                "total_hours": len(hourly_data[:hours])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting hourly forecast for {location}: {e}")
            raise
    
    async def detect_weather_changes(self, location: str) -> List[Dict[str, Any]]:
        """Detect significant weather changes and patterns."""
        try:
            # Get recent weather data
            recent_data = await weather_db.get_current_weather_history(location, hours=24)
            forecast = await weather_service.get_weather_forecast(location, days=3)
            
            changes = []
            
            if recent_data and forecast.forecast_days:
                current_avg_temp = statistics.mean([float(d['temperature_c']) for d in recent_data if d['temperature_c']])
                
                # Temperature change detection
                for i, day in enumerate(forecast.forecast_days[:3]):
                    temp_change = day.avg_temp_c - current_avg_temp
                    
                    if abs(temp_change) > 5:  # Significant temperature change
                        changes.append({
                            "type": "temperature_change",
                            "day": i + 1,
                            "current_temp": round(current_avg_temp, 1),
                            "forecast_temp": day.avg_temp_c,
                            "change": round(temp_change, 1),
                            "severity": "high" if abs(temp_change) > 10 else "medium",
                            "description": f"Temperature {'rise' if temp_change > 0 else 'drop'} of {abs(temp_change):.1f}°C expected"
                        })
                
                # Precipitation detection
                for i, day in enumerate(forecast.forecast_days[:3]):
                    if day.chance_of_rain > 70:
                        changes.append({
                            "type": "precipitation",
                            "day": i + 1,
                            "chance": day.chance_of_rain,
                            "amount_mm": day.total_precip_mm,
                            "severity": "high" if day.chance_of_rain > 90 else "medium",
                            "description": f"High chance ({day.chance_of_rain}%) of {day.total_precip_mm}mm precipitation"
                        })
                
                # Wind change detection
                if recent_data:
                    current_wind = statistics.mean([float(d.get('wind_speed_kph', 0)) for d in recent_data])
                    
                    for i, day in enumerate(forecast.forecast_days[:3]):
                        if day.max_wind_kph > current_wind * 1.5 and day.max_wind_kph > 25:
                            changes.append({
                                "type": "wind_change",
                                "day": i + 1,
                                "current_wind": round(current_wind, 1),
                                "forecast_wind": day.max_wind_kph,
                                "severity": "high" if day.max_wind_kph > 50 else "medium",
                                "description": f"Strong winds up to {day.max_wind_kph} km/h expected"
                            })
            
            self.logger.info(f"Detected {len(changes)} weather changes for {location}")
            return changes
            
        except Exception as e:
            self.logger.error(f"Error detecting weather changes for {location}: {e}")
            return []
    
    def _analyze_historical_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical weather trends."""
        if not historical_data:
            return {}
        
        try:
            temperatures = [float(d['temperature_c']) for d in historical_data if d.get('temperature_c')]
            humidity_values = [int(d['humidity']) for d in historical_data if d.get('humidity')]
            pressure_values = [float(d['pressure_mb']) for d in historical_data if d.get('pressure_mb')]
            
            trends = {}
            
            if temperatures:
                trends['temperature'] = {
                    'mean': round(statistics.mean(temperatures), 1),
                    'trend': self._calculate_trend(temperatures),
                    'volatility': round(statistics.stdev(temperatures) if len(temperatures) > 1 else 0, 1),
                    'range': round(max(temperatures) - min(temperatures), 1)
                }
            
            if humidity_values:
                trends['humidity'] = {
                    'mean': round(statistics.mean(humidity_values), 1),
                    'trend': self._calculate_trend(humidity_values)
                }
            
            if pressure_values:
                trends['pressure'] = {
                    'mean': round(statistics.mean(pressure_values), 1),
                    'trend': self._calculate_trend(pressure_values)
                }
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return {}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 3:
            return "stable"
        
        # Simple trend calculation using first and last thirds
        first_third = statistics.mean(values[:len(values)//3])
        last_third = statistics.mean(values[-len(values)//3:])
        
        diff = last_third - first_third
        
        if abs(diff) < 0.5:
            return "stable"
        elif diff > 0:
            return "rising"
        else:
            return "falling"
    
    def _calculate_confidence(self, historical_data: List[Dict[str, Any]]) -> float:
        """Calculate prediction confidence based on data availability and patterns."""
        if not historical_data:
            return 0.3  # Low confidence without historical data
        
        # Base confidence on amount and consistency of historical data
        data_points = len(historical_data)
        
        if data_points < 5:
            return 0.4
        elif data_points < 20:
            return 0.6
        elif data_points < 50:
            return 0.8
        else:
            return 0.9
    
    async def _predict_weather_day(self, location: str, reference_day: Optional[ForecastDay], 
                                 trends: Dict[str, Any], days_ahead: int) -> ForecastDay:
        """Predict weather for a specific day using trends and models."""
        try:
            # Use simple prediction model for now
            base_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            if reference_day:
                # Base prediction on the last known forecast day
                temp_trend_factor = trends.get('temperature', {}).get('trend', 'stable')
                
                if temp_trend_factor == 'rising':
                    temp_adjustment = min(2.0, days_ahead * 0.5)
                elif temp_trend_factor == 'falling':
                    temp_adjustment = max(-2.0, -days_ahead * 0.5)
                else:
                    temp_adjustment = 0
                
                predicted_max = reference_day.max_temp_c + temp_adjustment
                predicted_min = reference_day.min_temp_c + temp_adjustment
                predicted_avg = (predicted_max + predicted_min) / 2
            
            else:
                # Use seasonal averages if no reference
                predicted_max = 20.0  # Default values
                predicted_min = 10.0
                predicted_avg = 15.0
            
            return ForecastDay(
                date=base_date,
                max_temp_c=round(predicted_max, 1),
                max_temp_f=round(predicted_max * 9/5 + 32, 1),
                min_temp_c=round(predicted_min, 1),
                min_temp_f=round(predicted_min * 9/5 + 32, 1),
                avg_temp_c=round(predicted_avg, 1),
                avg_temp_f=round(predicted_avg * 9/5 + 32, 1),
                condition="Partly cloudy",  # Default prediction
                chance_of_rain=30,  # Conservative estimate
                chance_of_snow=0,
                max_wind_kph=15.0,
                max_wind_mph=9.3,
                total_precip_mm=0.0,
                total_precip_in=0.0,
                avg_humidity=65,
                uv_index=5.0
            )
            
        except Exception as e:
            self.logger.error(f"Error predicting weather day: {e}")
            raise
    
    def _interpolate_hourly_temperature(self, min_temp: float, max_temp: float, hour: int) -> float:
        """Interpolate hourly temperature from daily min/max."""
        # Simple sinusoidal interpolation (max at 14:00, min at 06:00)
        import math
        
        # Assume max temp at 2 PM (14:00) and min temp at 6 AM (06:00)
        peak_hour = 14
        trough_hour = 6
        
        # Calculate position in temperature cycle
        if hour >= trough_hour and hour <= peak_hour:
            # Rising temperature
            progress = (hour - trough_hour) / (peak_hour - trough_hour)
            angle = progress * math.pi / 2  # 0 to π/2
            temp = min_temp + (max_temp - min_temp) * math.sin(angle)
        else:
            # Falling temperature
            if hour > peak_hour:
                progress = (hour - peak_hour) / (24 - peak_hour + trough_hour)
            else:
                progress = (hour + 24 - peak_hour) / (24 - peak_hour + trough_hour)
            
            angle = math.pi / 2 + progress * math.pi / 2  # π/2 to π
            temp = min_temp + (max_temp - min_temp) * math.sin(angle)
        
        return temp
    
    # Prediction model implementations
    async def _simple_trend_prediction(self, data: List[float], steps: int) -> List[float]:
        """Simple linear trend prediction."""
        if len(data) < 2:
            return [data[-1] if data else 0] * steps
        
        # Calculate simple trend
        trend = (data[-1] - data[0]) / (len(data) - 1)
        
        predictions = []
        for i in range(1, steps + 1):
            predicted = data[-1] + trend * i
            predictions.append(predicted)
        
        return predictions
    
    async def _moving_average_prediction(self, data: List[float], steps: int, window: int = 5) -> List[float]:
        """Moving average based prediction."""
        if len(data) < window:
            return await self._simple_trend_prediction(data, steps)
        
        # Calculate moving average
        recent_avg = statistics.mean(data[-window:])
        
        # For simplicity, assume the moving average continues
        return [recent_avg] * steps
    
    async def _weighted_prediction(self, data: List[float], steps: int) -> List[float]:
        """Weighted prediction giving more importance to recent data."""
        if len(data) < 3:
            return await self._simple_trend_prediction(data, steps)
        
        # Create weights (more recent = higher weight)
        weights = [i + 1 for i in range(len(data))]
        
        # Calculate weighted average
        weighted_sum = sum(d * w for d, w in zip(data, weights))
        total_weight = sum(weights)
        weighted_avg = weighted_sum / total_weight
        
        # Simple trend from weighted average
        trend = (data[-1] - weighted_avg) * 0.1  # Dampened trend
        
        predictions = []
        for i in range(1, steps + 1):
            predicted = weighted_avg + trend * i
            predictions.append(predicted)
        
        return predictions


# Global forecast service instance
forecast_service = ForecastService()