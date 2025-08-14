"""Database service for storing weather data."""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

from .config import config
from .models import CurrentWeather, WeatherForecast, WeatherAlert, WeatherThreshold
from .logger import get_logger


class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class WeatherDatabase:
    """SQLite database service for weather data."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = get_logger("database")
        self.db_path = db_path or self._get_db_path()
        self._lock = asyncio.Lock()
        self._init_database()
    
    def _get_db_path(self) -> str:
        """Get database path from configuration."""
        if config.database_url.startswith("sqlite:///"):
            return config.database_url.replace("sqlite:///", "")
        return "weather.db"
    
    def _init_database(self):
        """Initialize database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Current weather table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS current_weather (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        location_name TEXT NOT NULL,
                        location_country TEXT NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        temperature_c REAL NOT NULL,
                        temperature_f REAL NOT NULL,
                        condition TEXT NOT NULL,
                        humidity INTEGER NOT NULL,
                        feels_like_c REAL NOT NULL,
                        feels_like_f REAL NOT NULL,
                        wind_speed_kph REAL NOT NULL,
                        wind_speed_mph REAL NOT NULL,
                        wind_direction TEXT NOT NULL,
                        wind_degree INTEGER NOT NULL,
                        pressure_mb REAL NOT NULL,
                        pressure_in REAL NOT NULL,
                        visibility_km REAL NOT NULL,
                        visibility_miles REAL NOT NULL,
                        uv_index REAL NOT NULL,
                        last_updated TIMESTAMP NOT NULL,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_source TEXT DEFAULT 'weatherapi',
                        raw_data TEXT
                    )
                """)
                
                # Weather forecasts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS weather_forecasts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        location_name TEXT NOT NULL,
                        forecast_date DATE NOT NULL,
                        max_temp_c REAL NOT NULL,
                        max_temp_f REAL NOT NULL,
                        min_temp_c REAL NOT NULL,
                        min_temp_f REAL NOT NULL,
                        avg_temp_c REAL NOT NULL,
                        avg_temp_f REAL NOT NULL,
                        condition TEXT NOT NULL,
                        chance_of_rain INTEGER DEFAULT 0,
                        chance_of_snow INTEGER DEFAULT 0,
                        max_wind_kph REAL NOT NULL,
                        max_wind_mph REAL NOT NULL,
                        total_precip_mm REAL DEFAULT 0,
                        total_precip_in REAL DEFAULT 0,
                        avg_humidity INTEGER NOT NULL,
                        uv_index REAL NOT NULL,
                        sunrise TEXT,
                        sunset TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(location_name, forecast_date)
                    )
                """)
                
                # Weather alerts table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS weather_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE,
                        location_name TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                """)
                
                # Weather thresholds table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS weather_thresholds (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        location_name TEXT NOT NULL,
                        metric TEXT NOT NULL,
                        min_value REAL,
                        max_value REAL,
                        alert_message TEXT NOT NULL,
                        is_enabled BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(location_name, metric)
                    )
                """)
                
                # Indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_current_weather_location ON current_weather(location_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_current_weather_recorded ON current_weather(recorded_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_location_date ON weather_forecasts(location_name, forecast_date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_location ON weather_alerts(location_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_active ON weather_alerts(is_active)")
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    async def store_current_weather(self, weather: CurrentWeather) -> int:
        """Store current weather data."""
        async with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        INSERT INTO current_weather (
                            location_name, location_country, latitude, longitude,
                            temperature_c, temperature_f, condition, humidity,
                            feels_like_c, feels_like_f, wind_speed_kph, wind_speed_mph,
                            wind_direction, wind_degree, pressure_mb, pressure_in,
                            visibility_km, visibility_miles, uv_index, last_updated,
                            data_source, raw_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        weather.location.name, weather.location.country,
                        weather.location.latitude, weather.location.longitude,
                        weather.temperature_c, weather.temperature_f,
                        weather.condition, weather.humidity,
                        weather.feels_like_c, weather.feels_like_f,
                        weather.wind_speed_kph, weather.wind_speed_mph,
                        weather.wind_direction, weather.wind_degree,
                        weather.pressure_mb, weather.pressure_in,
                        weather.visibility_km, weather.visibility_miles,
                        weather.uv_index, weather.last_updated,
                        weather.data_source, json.dumps(weather.dict())
                    ))
                    record_id = cursor.lastrowid
                    conn.commit()
                    
                    self.logger.debug(f"Stored weather data for {weather.location.name} (ID: {record_id})")
                    return record_id
                    
            except sqlite3.Error as e:
                self.logger.error(f"Error storing weather data: {e}")
                raise DatabaseError(f"Failed to store weather data: {e}")
    
    async def store_weather_forecast(self, forecast: WeatherForecast) -> int:
        """Store weather forecast data."""
        async with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    records_stored = 0
                    for day in forecast.forecast_days:
                        conn.execute("""
                            INSERT OR REPLACE INTO weather_forecasts (
                                location_name, forecast_date, max_temp_c, max_temp_f,
                                min_temp_c, min_temp_f, avg_temp_c, avg_temp_f,
                                condition, chance_of_rain, chance_of_snow,
                                max_wind_kph, max_wind_mph, total_precip_mm,
                                total_precip_in, avg_humidity, uv_index,
                                sunrise, sunset
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            forecast.location.name, day.date.date(),
                            day.max_temp_c, day.max_temp_f,
                            day.min_temp_c, day.min_temp_f,
                            day.avg_temp_c, day.avg_temp_f,
                            day.condition, day.chance_of_rain, day.chance_of_snow,
                            day.max_wind_kph, day.max_wind_mph,
                            day.total_precip_mm, day.total_precip_in,
                            day.avg_humidity, day.uv_index,
                            day.sunrise, day.sunset
                        ))
                        records_stored += 1
                    
                    conn.commit()
                    self.logger.debug(f"Stored {records_stored} forecast days for {forecast.location.name}")
                    return records_stored
                    
            except sqlite3.Error as e:
                self.logger.error(f"Error storing forecast data: {e}")
                raise DatabaseError(f"Failed to store forecast data: {e}")
    
    async def get_current_weather_history(self, location: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get current weather history for a location."""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM current_weather 
                    WHERE location_name = ? AND recorded_at >= ?
                    ORDER BY recorded_at DESC
                """, (location, since))
                
                records = [dict(row) for row in cursor.fetchall()]
                self.logger.debug(f"Retrieved {len(records)} weather history records for {location}")
                return records
                
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving weather history: {e}")
            raise DatabaseError(f"Failed to retrieve weather history: {e}")
    
    async def get_weather_trends(self, location: str, days: int = 7) -> Dict[str, Any]:
        """Get weather trends for analysis."""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        AVG(temperature_c) as avg_temp,
                        MIN(temperature_c) as min_temp,
                        MAX(temperature_c) as max_temp,
                        AVG(humidity) as avg_humidity,
                        AVG(pressure_mb) as avg_pressure,
                        AVG(wind_speed_kph) as avg_wind_speed,
                        COUNT(*) as data_points
                    FROM current_weather 
                    WHERE location_name = ? AND recorded_at >= ?
                """, (location, since))
                
                result = cursor.fetchone()
                if result:
                    trends = {
                        "location": location,
                        "period_days": days,
                        "avg_temperature_c": round(result[0], 1) if result[0] else 0,
                        "min_temperature_c": round(result[1], 1) if result[1] else 0,
                        "max_temperature_c": round(result[2], 1) if result[2] else 0,
                        "avg_humidity": round(result[3], 1) if result[3] else 0,
                        "avg_pressure_mb": round(result[4], 1) if result[4] else 0,
                        "avg_wind_speed_kph": round(result[5], 1) if result[5] else 0,
                        "data_points": result[6]
                    }
                    
                    self.logger.debug(f"Retrieved weather trends for {location}")
                    return trends
                else:
                    return {"location": location, "data_points": 0}
                    
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving weather trends: {e}")
            raise DatabaseError(f"Failed to retrieve weather trends: {e}")
    
    async def store_weather_alert(self, alert: WeatherAlert) -> int:
        """Store weather alert."""
        async with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        INSERT OR REPLACE INTO weather_alerts (
                            alert_id, location_name, alert_type, severity,
                            title, description, start_time, end_time, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        alert.id, alert.location, alert.alert_type,
                        alert.severity, alert.title, alert.description,
                        alert.start_time, alert.end_time, alert.is_active
                    ))
                    
                    record_id = cursor.lastrowid
                    conn.commit()
                    
                    self.logger.info(f"Stored weather alert: {alert.title} for {alert.location}")
                    return record_id
                    
            except sqlite3.Error as e:
                self.logger.error(f"Error storing weather alert: {e}")
                raise DatabaseError(f"Failed to store weather alert: {e}")
    
    async def get_active_alerts(self, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active weather alerts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if location:
                    cursor = conn.execute("""
                        SELECT * FROM weather_alerts 
                        WHERE location_name = ? AND is_active = 1
                        ORDER BY created_at DESC
                    """, (location,))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM weather_alerts 
                        WHERE is_active = 1
                        ORDER BY created_at DESC
                    """)
                
                alerts = [dict(row) for row in cursor.fetchall()]
                self.logger.debug(f"Retrieved {len(alerts)} active alerts")
                return alerts
                
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving active alerts: {e}")
            raise DatabaseError(f"Failed to retrieve active alerts: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old weather data."""
        async with self._lock:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                with sqlite3.connect(self.db_path) as conn:
                    # Clean up old current weather data
                    cursor = conn.execute("""
                        DELETE FROM current_weather 
                        WHERE recorded_at < ?
                    """, (cutoff_date,))
                    current_deleted = cursor.rowcount
                    
                    # Clean up old forecast data
                    cursor = conn.execute("""
                        DELETE FROM weather_forecasts 
                        WHERE created_at < ?
                    """, (cutoff_date,))
                    forecast_deleted = cursor.rowcount
                    
                    # Clean up old inactive alerts
                    cursor = conn.execute("""
                        DELETE FROM weather_alerts 
                        WHERE created_at < ? AND is_active = 0
                    """, (cutoff_date,))
                    alerts_deleted = cursor.rowcount
                    
                    conn.commit()
                    
                    self.logger.info(f"Cleanup completed: {current_deleted} weather records, {forecast_deleted} forecast records, {alerts_deleted} alerts deleted")
                    
            except sqlite3.Error as e:
                self.logger.error(f"Error during cleanup: {e}")
                raise DatabaseError(f"Failed to cleanup old data: {e}")
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM current_weather")
                current_weather_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM weather_forecasts")
                forecasts_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM weather_alerts WHERE is_active = 1")
                active_alerts_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(DISTINCT location_name) FROM current_weather")
                unique_locations = cursor.fetchone()[0]
                
                # Get database file size
                db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                
                return {
                    "current_weather_records": current_weather_count,
                    "forecast_records": forecasts_count,
                    "active_alerts": active_alerts_count,
                    "unique_locations": unique_locations,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / (1024 * 1024), 2)
                }
                
        except sqlite3.Error as e:
            self.logger.error(f"Error getting database stats: {e}")
            raise DatabaseError(f"Failed to get database stats: {e}")


# Global database instance
weather_db = WeatherDatabase()