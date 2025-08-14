"""Weather alert and notification system."""

import asyncio
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional, Set
import json
import hashlib

from .config import config
from .database import weather_db
from .models import WeatherAlert, WeatherThreshold, CurrentWeather
from .logger import get_logger


class AlertType:
    """Constants for alert types."""
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    HEAVY_RAIN = "heavy_rain"
    STRONG_WIND = "strong_wind"
    HUMIDITY_HIGH = "humidity_high"
    PRESSURE_DROP = "pressure_drop"
    UV_HIGH = "uv_high"
    VISIBILITY_LOW = "visibility_low"
    WEATHER_CHANGE = "weather_change"


class AlertSeverity:
    """Constants for alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WeatherAlertService:
    """Weather alert and monitoring service."""
    
    def __init__(self):
        self.logger = get_logger("alerts")
        self._active_alerts: Set[str] = set()
        self._alert_history: List[Dict[str, Any]] = []
        
        # Default thresholds
        self._default_thresholds = {
            "temperature_high": {"value": 35.0, "message": "High temperature alert"},
            "temperature_low": {"value": -10.0, "message": "Low temperature alert"},
            "wind_speed": {"value": 50.0, "message": "Strong wind alert"},
            "humidity": {"value": 90.0, "message": "High humidity alert"},
            "uv_index": {"value": 8.0, "message": "High UV index alert"},
            "visibility": {"value": 1.0, "message": "Low visibility alert"},
            "pressure_drop": {"value": 10.0, "message": "Significant pressure drop"}
        }
    
    async def check_weather_alerts(self, weather: CurrentWeather) -> List[WeatherAlert]:
        """Check current weather against alert thresholds."""
        alerts = []
        location = weather.location.name
        
        try:
            # Get custom thresholds for this location
            thresholds = await self._get_location_thresholds(location)
            
            # Check temperature alerts
            alerts.extend(await self._check_temperature_alerts(weather, thresholds))
            
            # Check wind alerts
            alerts.extend(await self._check_wind_alerts(weather, thresholds))
            
            # Check humidity alerts
            alerts.extend(await self._check_humidity_alerts(weather, thresholds))
            
            # Check UV alerts
            alerts.extend(await self._check_uv_alerts(weather, thresholds))
            
            # Check visibility alerts
            alerts.extend(await self._check_visibility_alerts(weather, thresholds))
            
            # Check pressure alerts
            alerts.extend(await self._check_pressure_alerts(weather, thresholds))
            
            # Store and process new alerts
            new_alerts = []
            for alert in alerts:
                alert_id = self._generate_alert_id(alert)
                
                if alert_id not in self._active_alerts:
                    alert.id = alert_id
                    await weather_db.store_weather_alert(alert)
                    self._active_alerts.add(alert_id)
                    new_alerts.append(alert)
                    
                    # Send notification for new alerts
                    await self._send_alert_notification(alert)
            
            if new_alerts:
                self.logger.info(f"Generated {len(new_alerts)} new alerts for {location}")
            
            return new_alerts
            
        except Exception as e:
            self.logger.error(f"Error checking alerts for {location}: {e}")
            return []
    
    async def setup_custom_threshold(self, location: str, metric: str, 
                                   min_value: Optional[float] = None,
                                   max_value: Optional[float] = None,
                                   alert_message: str = "") -> bool:
        """Set up custom alert threshold for a location."""
        try:
            threshold = WeatherThreshold(
                location=location,
                metric=metric,
                min_value=min_value,
                max_value=max_value,
                alert_message=alert_message or f"Custom {metric} alert for {location}"
            )
            
            # Store in database
            async with weather_db._lock:
                with weather_db._get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO weather_thresholds
                        (location_name, metric, min_value, max_value, alert_message, is_enabled)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (location, metric, min_value, max_value, alert_message, True))
                    conn.commit()
            
            self.logger.info(f"Set custom threshold for {location}: {metric}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting threshold: {e}")
            return False
    
    async def get_active_alerts_summary(self, location: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of active alerts."""
        try:
            active_alerts = await weather_db.get_active_alerts(location)
            
            # Group alerts by severity and type
            summary = {
                "total_alerts": len(active_alerts),
                "by_severity": {},
                "by_type": {},
                "by_location": {},
                "most_recent": None
            }
            
            for alert in active_alerts:
                # By severity
                severity = alert["severity"]
                summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
                
                # By type
                alert_type = alert["alert_type"]
                summary["by_type"][alert_type] = summary["by_type"].get(alert_type, 0) + 1
                
                # By location
                loc = alert["location_name"]
                summary["by_location"][loc] = summary["by_location"].get(loc, 0) + 1
                
                # Most recent
                if not summary["most_recent"] or alert["created_at"] > summary["most_recent"]["created_at"]:
                    summary["most_recent"] = alert
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting alerts summary: {e}")
            return {"error": str(e)}
    
    async def _get_location_thresholds(self, location: str) -> Dict[str, Dict[str, Any]]:
        """Get alert thresholds for a location."""
        try:
            # Get from database first
            custom_thresholds = {}
            async with weather_db._lock:
                with weather_db._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute("""
                        SELECT metric, min_value, max_value, alert_message
                        FROM weather_thresholds
                        WHERE location_name = ? AND is_enabled = 1
                    """, (location,))
                    
                    for row in cursor.fetchall():
                        custom_thresholds[row["metric"]] = {
                            "min_value": row["min_value"],
                            "max_value": row["max_value"],
                            "message": row["alert_message"]
                        }
            
            # Merge with defaults
            thresholds = self._default_thresholds.copy()
            for metric, values in custom_thresholds.items():
                thresholds[metric] = values
            
            return thresholds
            
        except Exception as e:
            self.logger.error(f"Error getting thresholds for {location}: {e}")
            return self._default_thresholds
    
    async def _check_temperature_alerts(self, weather: CurrentWeather, 
                                      thresholds: Dict[str, Dict[str, Any]]) -> List[WeatherAlert]:
        """Check temperature-based alerts."""
        alerts = []
        
        # High temperature
        if "temperature_high" in thresholds:
            threshold = thresholds["temperature_high"]["value"]
            if weather.temperature_c > threshold:
                alerts.append(WeatherAlert(
                    location=weather.location.name,
                    alert_type=AlertType.TEMPERATURE_HIGH,
                    severity=self._get_temperature_severity(weather.temperature_c, threshold),
                    title=f"High Temperature Alert - {weather.location.name}",
                    description=f"Temperature {weather.temperature_c}°C exceeds threshold {threshold}°C",
                    start_time=datetime.utcnow()
                ))
        
        # Low temperature
        if "temperature_low" in thresholds:
            threshold = thresholds["temperature_low"]["value"]
            if weather.temperature_c < threshold:
                alerts.append(WeatherAlert(
                    location=weather.location.name,
                    alert_type=AlertType.TEMPERATURE_LOW,
                    severity=self._get_temperature_severity(threshold, weather.temperature_c),
                    title=f"Low Temperature Alert - {weather.location.name}",
                    description=f"Temperature {weather.temperature_c}°C below threshold {threshold}°C",
                    start_time=datetime.utcnow()
                ))
        
        return alerts
    
    async def _check_wind_alerts(self, weather: CurrentWeather, 
                               thresholds: Dict[str, Dict[str, Any]]) -> List[WeatherAlert]:
        """Check wind-based alerts."""
        alerts = []
        
        if "wind_speed" in thresholds:
            threshold = thresholds["wind_speed"]["value"]
            if weather.wind_speed_kph > threshold:
                severity = AlertSeverity.HIGH if weather.wind_speed_kph > threshold * 1.5 else AlertSeverity.MEDIUM
                
                alerts.append(WeatherAlert(
                    location=weather.location.name,
                    alert_type=AlertType.STRONG_WIND,
                    severity=severity,
                    title=f"Strong Wind Alert - {weather.location.name}",
                    description=f"Wind speed {weather.wind_speed_kph} km/h exceeds threshold {threshold} km/h",
                    start_time=datetime.utcnow()
                ))
        
        return alerts
    
    async def _check_humidity_alerts(self, weather: CurrentWeather,
                                   thresholds: Dict[str, Dict[str, Any]]) -> List[WeatherAlert]:
        """Check humidity-based alerts."""
        alerts = []
        
        if "humidity" in thresholds:
            threshold = thresholds["humidity"]["value"]
            if weather.humidity > threshold:
                alerts.append(WeatherAlert(
                    location=weather.location.name,
                    alert_type=AlertType.HUMIDITY_HIGH,
                    severity=AlertSeverity.MEDIUM,
                    title=f"High Humidity Alert - {weather.location.name}",
                    description=f"Humidity {weather.humidity}% exceeds threshold {threshold}%",
                    start_time=datetime.utcnow()
                ))
        
        return alerts
    
    async def _check_uv_alerts(self, weather: CurrentWeather,
                             thresholds: Dict[str, Dict[str, Any]]) -> List[WeatherAlert]:
        """Check UV index alerts."""
        alerts = []
        
        if "uv_index" in thresholds:
            threshold = thresholds["uv_index"]["value"]
            if weather.uv_index > threshold:
                severity = AlertSeverity.HIGH if weather.uv_index > 10 else AlertSeverity.MEDIUM
                
                alerts.append(WeatherAlert(
                    location=weather.location.name,
                    alert_type=AlertType.UV_HIGH,
                    severity=severity,
                    title=f"High UV Index Alert - {weather.location.name}",
                    description=f"UV index {weather.uv_index} exceeds safe threshold {threshold}",
                    start_time=datetime.utcnow()
                ))
        
        return alerts
    
    async def _check_visibility_alerts(self, weather: CurrentWeather,
                                     thresholds: Dict[str, Dict[str, Any]]) -> List[WeatherAlert]:
        """Check visibility alerts."""
        alerts = []
        
        if "visibility" in thresholds:
            threshold = thresholds["visibility"]["value"]
            if weather.visibility_km < threshold:
                severity = AlertSeverity.HIGH if weather.visibility_km < 0.5 else AlertSeverity.MEDIUM
                
                alerts.append(WeatherAlert(
                    location=weather.location.name,
                    alert_type=AlertType.VISIBILITY_LOW,
                    severity=severity,
                    title=f"Low Visibility Alert - {weather.location.name}",
                    description=f"Visibility {weather.visibility_km} km below threshold {threshold} km",
                    start_time=datetime.utcnow()
                ))
        
        return alerts
    
    async def _check_pressure_alerts(self, weather: CurrentWeather,
                                   thresholds: Dict[str, Dict[str, Any]]) -> List[WeatherAlert]:
        """Check pressure change alerts."""
        alerts = []
        
        try:
            # Get recent pressure data to detect drops
            recent_data = await weather_db.get_current_weather_history(weather.location.name, hours=6)
            
            if len(recent_data) > 1 and "pressure_drop" in thresholds:
                recent_pressures = [float(d['pressure_mb']) for d in recent_data if d.get('pressure_mb')]
                
                if len(recent_pressures) > 1:
                    pressure_drop = max(recent_pressures) - weather.pressure_mb
                    threshold = thresholds["pressure_drop"]["value"]
                    
                    if pressure_drop > threshold:
                        alerts.append(WeatherAlert(
                            location=weather.location.name,
                            alert_type=AlertType.PRESSURE_DROP,
                            severity=AlertSeverity.MEDIUM,
                            title=f"Pressure Drop Alert - {weather.location.name}",
                            description=f"Pressure dropped {pressure_drop:.1f} mb in recent hours",
                            start_time=datetime.utcnow()
                        ))
        
        except Exception as e:
            self.logger.error(f"Error checking pressure alerts: {e}")
        
        return alerts
    
    def _get_temperature_severity(self, temp1: float, temp2: float) -> str:
        """Determine severity based on temperature difference."""
        diff = abs(temp1 - temp2)
        
        if diff > 15:
            return AlertSeverity.CRITICAL
        elif diff > 10:
            return AlertSeverity.HIGH
        elif diff > 5:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _generate_alert_id(self, alert: WeatherAlert) -> str:
        """Generate unique alert ID."""
        content = f"{alert.location}{alert.alert_type}{alert.start_time.date()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def _send_alert_notification(self, alert: WeatherAlert):
        """Send alert notification via email."""
        try:
            if not config.notification_email_to or not config.email_username:
                self.logger.debug("Email notification not configured")
                return
            
            # Create email content
            subject = f"Weather Alert: {alert.title}"
            body = self._format_alert_email(alert)
            
            # Send email
            await self._send_email(subject, body, config.notification_email_to)
            
            self.logger.info(f"Sent alert notification for {alert.location}: {alert.alert_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {e}")
    
    def _format_alert_email(self, alert: WeatherAlert) -> str:
        """Format alert as email content."""
        return f"""
Weather Alert Notification

Location: {alert.location}
Alert Type: {alert.alert_type.replace('_', ' ').title()}
Severity: {alert.severity.upper()}
Time: {alert.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}

Description:
{alert.description}

This is an automated weather alert from your Weather Monitoring System.
        """.strip()
    
    async def _send_email(self, subject: str, body: str, to_email: str):
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = config.email_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(config.email_smtp_host, config.email_smtp_port) as server:
                server.starttls()
                server.login(config.email_username, config.email_password)
                server.send_message(msg)
            
            self.logger.debug(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise


# Global alert service instance
alert_service = WeatherAlertService()