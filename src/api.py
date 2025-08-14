"""Flask web API for Weather Application."""

from flask import Flask, jsonify, request, render_template_string
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import json
from typing import Dict, Any, List

from .config import config
from .weather_service import weather_service
from .forecast_service import forecast_service
from .alert_service import alert_service
from .database import weather_db
from .logger import get_logger


def async_route(f):
    """Decorator to handle async routes in Flask."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


class WeatherAPI:
    """Flask-based Weather API."""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.logger = get_logger("api")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.route('/')
        def home():
            """API home page with documentation."""
            return render_template_string(API_DOCUMENTATION_TEMPLATE)
        
        @self.app.route('/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            })
        
        @self.app.route('/api/weather/<location>')
        @async_route
        async def get_current_weather(location: str):
            """Get current weather for a location."""
            try:
                weather = await weather_service.get_current_weather(location)
                
                # Check for alerts
                alerts = await alert_service.check_weather_alerts(weather)
                
                # Store in database
                await weather_db.store_current_weather(weather)
                
                return jsonify({
                    "success": True,
                    "data": {
                        "weather": weather.dict(),
                        "alerts": [alert.dict() for alert in alerts]
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting weather for {location}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/forecast/<location>')
        @async_route
        async def get_weather_forecast(location: str):
            """Get weather forecast for a location."""
            try:
                days = request.args.get('days', 5, type=int)
                days = min(max(days, 1), 10)  # Limit between 1-10 days
                
                forecast = await weather_service.get_weather_forecast(location, days)
                await weather_db.store_weather_forecast(forecast)
                
                return jsonify({
                    "success": True,
                    "data": forecast.dict(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting forecast for {location}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/forecast/<location>/extended')
        @async_route
        async def get_extended_forecast(location: str):
            """Get extended forecast with predictions."""
            try:
                days = request.args.get('days', 10, type=int)
                days = min(max(days, 1), 30)  # Limit between 1-30 days
                
                forecast = await forecast_service.get_extended_forecast(location, days)
                
                return jsonify({
                    "success": True,
                    "data": forecast,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting extended forecast for {location}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/forecast/<location>/hourly')
        @async_route
        async def get_hourly_forecast(location: str):
            """Get hourly forecast."""
            try:
                hours = request.args.get('hours', 24, type=int)
                hours = min(max(hours, 1), 168)  # Limit between 1-168 hours (1 week)
                
                forecast = await forecast_service.get_hourly_forecast(location, hours)
                
                return jsonify({
                    "success": True,
                    "data": forecast,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting hourly forecast for {location}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/weather/<location>/changes')
        @async_route
        async def get_weather_changes(location: str):
            """Get detected weather changes."""
            try:
                changes = await forecast_service.detect_weather_changes(location)
                
                return jsonify({
                    "success": True,
                    "data": {
                        "location": location,
                        "changes": changes,
                        "total_changes": len(changes)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting weather changes for {location}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/weather/<location>/history')
        @async_route
        async def get_weather_history(location: str):
            """Get weather history for a location."""
            try:
                hours = request.args.get('hours', 24, type=int)
                hours = min(max(hours, 1), 168)  # Limit between 1-168 hours
                
                history = await weather_db.get_current_weather_history(location, hours)
                
                return jsonify({
                    "success": True,
                    "data": {
                        "location": location,
                        "hours": hours,
                        "records": history,
                        "total_records": len(history)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting weather history for {location}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/weather/<location>/trends')
        @async_route
        async def get_weather_trends(location: str):
            """Get weather trends analysis."""
            try:
                days = request.args.get('days', 7, type=int)
                days = min(max(days, 1), 30)  # Limit between 1-30 days
                
                trends = await weather_db.get_weather_trends(location, days)
                
                return jsonify({
                    "success": True,
                    "data": trends,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting weather trends for {location}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/alerts')
        @async_route
        async def get_alerts():
            """Get active alerts."""
            try:
                location = request.args.get('location')
                summary = await alert_service.get_active_alerts_summary(location)
                
                return jsonify({
                    "success": True,
                    "data": summary,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting alerts: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/alerts/setup', methods=['POST'])
        @async_route
        async def setup_alert_threshold():
            """Setup custom alert threshold."""
            try:
                data = request.get_json()
                
                required_fields = ['location', 'metric']
                if not all(field in data for field in required_fields):
                    return jsonify({
                        "success": False,
                        "error": "Missing required fields: location, metric",
                        "timestamp": datetime.utcnow().isoformat()
                    }), 400
                
                success = await alert_service.setup_custom_threshold(
                    location=data['location'],
                    metric=data['metric'],
                    min_value=data.get('min_value'),
                    max_value=data.get('max_value'),
                    alert_message=data.get('alert_message', '')
                )
                
                return jsonify({
                    "success": success,
                    "message": "Alert threshold configured" if success else "Failed to configure threshold",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error setting up alert threshold: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/weather/bulk')
        @async_route
        async def get_bulk_weather():
            """Get weather for multiple locations."""
            try:
                locations = request.args.get('locations', '').split(',')
                locations = [loc.strip() for loc in locations if loc.strip()]
                
                if not locations:
                    return jsonify({
                        "success": False,
                        "error": "No locations provided",
                        "timestamp": datetime.utcnow().isoformat()
                    }), 400
                
                result, weather_data = await weather_service.get_multiple_locations_weather(locations)
                
                # Store successful results
                for location, weather in weather_data.items():
                    if weather:
                        await weather_db.store_current_weather(weather)
                
                return jsonify({
                    "success": True,
                    "data": {
                        "weather_data": {loc: weather.dict() for loc, weather in weather_data.items()},
                        "summary": result.dict()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting bulk weather: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/api/stats')
        @async_route
        async def get_database_stats():
            """Get database and system statistics."""
            try:
                stats = await weather_db.get_database_stats()
                
                return jsonify({
                    "success": True,
                    "data": {
                        "database": stats,
                        "configured_cities": config.default_cities,
                        "system": {
                            "update_interval_minutes": config.update_interval_minutes,
                            "cache_ttl_seconds": config.cache_ttl_seconds,
                            "max_retries": config.max_retries
                        }
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                self.logger.error(f"API error getting stats: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }), 500
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "success": False,
                "error": "Endpoint not found",
                "timestamp": datetime.utcnow().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "error": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            }), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the Flask application."""
        self.logger.info(f"Starting Weather API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# API Documentation Template
API_DOCUMENTATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Weather API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #2c5aa0; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; }
        .endpoint { background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .method { background-color: #3498db; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
        .method.post { background-color: #e74c3c; }
        code { background-color: #ecf0f1; padding: 2px 4px; border-radius: 3px; }
        pre { background-color: #2c3e50; color: white; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>🌤️ Weather API Documentation</h1>
    
    <h2>Base URL</h2>
    <p>All API endpoints are relative to the base URL of this server.</p>
    
    <h2>Authentication</h2>
    <p>Currently no authentication required. All endpoints are publicly accessible.</p>
    
    <h2>Response Format</h2>
    <p>All endpoints return JSON with the following structure:</p>
    <pre>{
  "success": true/false,
  "data": { ... },
  "error": "error message if success=false",
  "timestamp": "2023-01-01T12:00:00"
}</pre>
    
    <h2>Endpoints</h2>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/health</code>
        <p>Health check endpoint</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/weather/{location}</code>
        <p>Get current weather for a location</p>
        <p><strong>Example:</strong> <code>/api/weather/London</code></p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/forecast/{location}?days=5</code>
        <p>Get weather forecast (1-10 days)</p>
        <p><strong>Parameters:</strong> days (optional, default: 5)</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/forecast/{location}/extended?days=10</code>
        <p>Get extended forecast with predictions (1-30 days)</p>
        <p><strong>Parameters:</strong> days (optional, default: 10)</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/forecast/{location}/hourly?hours=24</code>
        <p>Get hourly forecast (1-168 hours)</p>
        <p><strong>Parameters:</strong> hours (optional, default: 24)</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/weather/{location}/changes</code>
        <p>Get detected weather changes and patterns</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/weather/{location}/history?hours=24</code>
        <p>Get weather history (1-168 hours)</p>
        <p><strong>Parameters:</strong> hours (optional, default: 24)</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/weather/{location}/trends?days=7</code>
        <p>Get weather trends analysis (1-30 days)</p>
        <p><strong>Parameters:</strong> days (optional, default: 7)</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/alerts?location=optional</code>
        <p>Get active weather alerts</p>
        <p><strong>Parameters:</strong> location (optional)</p>
    </div>
    
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/alerts/setup</code>
        <p>Setup custom alert threshold</p>
        <p><strong>Body:</strong> {"location": "City", "metric": "temperature_high", "max_value": 35, "alert_message": "Hot weather!"}</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/weather/bulk?locations=London,Paris,Tokyo</code>
        <p>Get weather for multiple locations</p>
        <p><strong>Parameters:</strong> locations (comma-separated)</p>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>/api/stats</code>
        <p>Get database and system statistics</p>
    </div>
    
    <h2>Rate Limiting</h2>
    <p>API requests are rate limited to prevent abuse. Current limit: 100 requests per minute per IP.</p>
    
    <h2>Error Codes</h2>
    <ul>
        <li><strong>400:</strong> Bad Request - Invalid parameters</li>
        <li><strong>404:</strong> Not Found - Endpoint doesn't exist</li>
        <li><strong>500:</strong> Internal Server Error - Server-side error</li>
    </ul>
</body>
</html>
"""

# Global API instance
weather_api = WeatherAPI()