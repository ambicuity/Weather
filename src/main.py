"""Main weather application with production features."""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import json
import click

from .config import config
from .weather_service import weather_service
from .forecast_service import forecast_service
from .alert_service import alert_service
from .database import weather_db
from .api import weather_api
from .logger import get_logger


class WeatherApp:
    """Main weather application with enhanced features."""
    
    def __init__(self):
        self.logger = get_logger("app")
    
    async def update_weather_data(self, locations: List[str] = None) -> bool:
        """Update weather data for specified locations."""
        if not locations:
            locations = config.default_cities
        
        self.logger.info(f"Starting weather update for {len(locations)} locations")
        
        try:
            # Fetch weather data
            result, weather_data = await weather_service.get_multiple_locations_weather(locations)
            
            # Store successful results in database and check alerts
            alerts_generated = []
            for location, weather in weather_data.items():
                if weather:
                    # Store weather data
                    await weather_db.store_current_weather(weather)
                    
                    # Check for alerts
                    location_alerts = await alert_service.check_weather_alerts(weather)
                    alerts_generated.extend(location_alerts)
            
            self.logger.info(f"Weather update completed: {result.locations_updated}")
            if alerts_generated:
                self.logger.info(f"Generated {len(alerts_generated)} new weather alerts")
            
            # Generate updated CSV and README
            await self._update_output_files(weather_data)
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"Error during weather update: {e}")
            return False
    
    async def get_comprehensive_forecast(self, location: str, days: int = 10) -> Dict[str, Any]:
        """Get comprehensive forecast including predictions and analysis."""
        try:
            # Get extended forecast
            extended_forecast = await forecast_service.get_extended_forecast(location, days)
            
            # Get weather changes
            changes = await forecast_service.detect_weather_changes(location)
            
            # Get historical trends
            trends = await weather_db.get_weather_trends(location, days=7)
            
            return {
                "location": location,
                "forecast": extended_forecast,
                "detected_changes": changes,
                "historical_trends": trends,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive forecast for {location}: {e}")
            raise
    
    async def setup_monitoring(self, location: str, thresholds: Dict[str, Any]) -> bool:
        """Setup weather monitoring for a location."""
        try:
            success = True
            
            for metric, config_data in thresholds.items():
                result = await alert_service.setup_custom_threshold(
                    location=location,
                    metric=metric,
                    min_value=config_data.get("min_value"),
                    max_value=config_data.get("max_value"),
                    alert_message=config_data.get("message", f"{metric} threshold for {location}")
                )
                
                if not result:
                    success = False
                    self.logger.error(f"Failed to setup {metric} threshold for {location}")
                else:
                    self.logger.info(f"Setup {metric} monitoring for {location}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error setting up monitoring for {location}: {e}")
            return False
    
    async def _update_output_files(self, weather_data: dict):
        """Update CSV and README files with latest weather data."""
        try:
            # Update CSV file
            csv_content = []
            for location, weather in weather_data.items():
                if weather:
                    csv_content.append(f"{weather.location.name},{weather.temperature_c},{weather.condition}")
            
            if csv_content:
                with open("weather_updates.csv", "w", encoding="utf-8") as f:
                    f.write("\n".join(csv_content) + "\n")
                self.logger.info("Updated weather_updates.csv")
            
            # Update README.md
            await self._update_readme(weather_data)
            
        except Exception as e:
            self.logger.error(f"Error updating output files: {e}")
    
    async def _update_readme(self, weather_data: dict):
        """Update README.md with enhanced weather table."""
        try:
            # Read current README
            with open("README.md", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Build enhanced weather table
            table_rows = ["<table><tr><th>City</th><th>Temperature (°C)</th><th>Condition</th><th>Humidity (%)</th><th>Wind (km/h)</th><th>Pressure (mb)</th><th>Last Updated</th></tr>"]
            
            for location, weather in weather_data.items():
                if weather:
                    last_updated = weather.last_updated.strftime("%Y-%m-%d %H:%M")
                    table_rows.append(
                        f"<tr><td>{weather.location.name}</td>"
                        f"<td>{weather.temperature_c}</td>"
                        f"<td>{weather.condition}</td>"
                        f"<td>{weather.humidity}</td>"
                        f"<td>{weather.wind_speed_kph}</td>"
                        f"<td>{weather.pressure_mb}</td>"
                        f"<td>{last_updated}</td></tr>"
                    )
            
            table_rows.append("</table>")
            weather_table = "".join(table_rows)
            
            # Replace content between markers
            start_marker = "<!-- WEATHER-UPDATE-START -->"
            end_marker = "<!-- WEATHER-UPDATE-END -->"
            
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                new_content = (
                    content[:start_idx + len(start_marker)] +
                    "\n" + weather_table + "\n" +
                    content[end_idx:]
                )
                
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                self.logger.info("Updated README.md with enhanced weather data")
            
        except Exception as e:
            self.logger.error(f"Error updating README: {e}")
    
    async def get_weather_summary(self) -> dict:
        """Get a comprehensive summary of current weather status."""
        try:
            db_stats = await weather_db.get_database_stats()
            alerts_summary = await alert_service.get_active_alerts_summary()
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "database_stats": db_stats,
                "alerts_summary": alerts_summary,
                "configured_locations": len(config.default_cities),
                "default_cities": config.default_cities,
                "system_config": {
                    "update_interval": config.update_interval_minutes,
                    "cache_ttl": config.cache_ttl_seconds,
                    "max_retries": config.max_retries
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting weather summary: {e}")
            return {"error": str(e)}


@click.group()
def cli():
    """Weather Application CLI - Production-level weather monitoring and forecasting."""
    pass


@cli.command()
@click.option('--locations', '-l', multiple=True, help='Specific locations to update')
@click.option('--all-default', '-a', is_flag=True, help='Update all default cities')
def update(locations, all_default):
    """Update weather data for specified locations."""
    async def run_update():
        app = WeatherApp()
        if all_default or not locations:
            success = await app.update_weather_data()
        else:
            success = await app.update_weather_data(list(locations))
        
        if success:
            click.echo("✅ Weather update completed successfully")
            return 0
        else:
            click.echo("❌ Weather update failed")
            return 1
    
    result = asyncio.run(run_update())
    sys.exit(result)


@cli.command()
@click.option('--location', '-l', required=True, help='Location for forecast')
@click.option('--days', '-d', default=10, help='Number of days to forecast')
@click.option('--output', '-o', help='Output file for forecast data')
def forecast(location, days, output):
    """Get comprehensive weather forecast for a location."""
    async def run_forecast():
        app = WeatherApp()
        try:
            forecast_data = await app.get_comprehensive_forecast(location, days)
            
            if output:
                with open(output, 'w') as f:
                    json.dump(forecast_data, f, indent=2, default=str)
                click.echo(f"📊 Forecast data saved to {output}")
            else:
                click.echo(f"📊 {days}-day forecast for {location}:")
                click.echo(json.dumps(forecast_data, indent=2, default=str))
            
        except Exception as e:
            click.echo(f"❌ Forecast error: {e}")
            return 1
        
        return 0
    
    result = asyncio.run(run_forecast())
    sys.exit(result)


@cli.command()
@click.option('--location', '-l', required=True, help='Location to monitor')
@click.option('--temp-high', type=float, help='High temperature threshold')
@click.option('--temp-low', type=float, help='Low temperature threshold')
@click.option('--wind-speed', type=float, help='Wind speed threshold (km/h)')
@click.option('--humidity', type=float, help='Humidity threshold (%)')
def monitor(location, temp_high, temp_low, wind_speed, humidity):
    """Setup weather monitoring thresholds for a location."""
    async def run_monitor():
        app = WeatherApp()
        
        thresholds = {}
        if temp_high is not None:
            thresholds['temperature_high'] = {
                'max_value': temp_high,
                'message': f'High temperature alert for {location}'
            }
        
        if temp_low is not None:
            thresholds['temperature_low'] = {
                'min_value': temp_low,
                'message': f'Low temperature alert for {location}'
            }
        
        if wind_speed is not None:
            thresholds['wind_speed'] = {
                'max_value': wind_speed,
                'message': f'Strong wind alert for {location}'
            }
        
        if humidity is not None:
            thresholds['humidity'] = {
                'max_value': humidity,
                'message': f'High humidity alert for {location}'
            }
        
        if not thresholds:
            click.echo("❌ No thresholds specified")
            return 1
        
        success = await app.setup_monitoring(location, thresholds)
        if success:
            click.echo(f"✅ Monitoring setup for {location}")
            return 0
        else:
            click.echo(f"❌ Failed to setup monitoring for {location}")
            return 1
    
    result = asyncio.run(run_monitor())
    sys.exit(result)


@cli.command()
@click.option('--location', '-l', help='Specific location for summary')
def summary(location):
    """Show comprehensive weather summary."""
    async def run_summary():
        app = WeatherApp()
        try:
            summary_data = await app.get_weather_summary()
            click.echo("📊 Weather System Summary:")
            click.echo(json.dumps(summary_data, indent=2, default=str))
        except Exception as e:
            click.echo(f"❌ Summary error: {e}")
            return 1
        
        return 0
    
    result = asyncio.run(run_summary())
    sys.exit(result)


@cli.command()
@click.option('--days', '-d', default=30, help='Days of data to keep')
def cleanup(days):
    """Clean up old weather data."""
    async def run_cleanup():
        try:
            await weather_db.cleanup_old_data(days)
            click.echo(f"✅ Cleanup completed for data older than {days} days")
            return 0
        except Exception as e:
            click.echo(f"❌ Cleanup error: {e}")
            return 1
    
    result = asyncio.run(run_cleanup())
    sys.exit(result)


@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='Host to bind to')
@click.option('--port', '-p', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def serve(host, port, debug):
    """Start the weather API server."""
    try:
        click.echo(f"🌐 Starting Weather API server on {host}:{port}")
        weather_api.run(host=host, port=port, debug=debug)
    except Exception as e:
        click.echo(f"❌ Server error: {e}")
        sys.exit(1)


@cli.command()
@click.option('--daemon', '-d', is_flag=True, help='Run as daemon')
def scheduler(daemon):
    """Start the weather monitoring scheduler."""
    try:
        # Import here to avoid circular imports
        from .scheduler import weather_scheduler
        
        click.echo("⏰ Starting Weather Scheduler")
        
        if daemon:
            # In a real production environment, you'd use proper daemonization
            click.echo("🔧 Daemon mode not implemented - running in foreground")
        
        weather_scheduler.start()
        
        # Keep running
        try:
            while weather_scheduler._running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n⏹️  Stopping scheduler...")
            weather_scheduler.stop()
        
    except Exception as e:
        click.echo(f"❌ Scheduler error: {e}")
        sys.exit(1)


@cli.command()
def status():
    """Show scheduler and system status."""
    try:
        # Import here to avoid circular imports
        from .scheduler import weather_scheduler
        
        status_data = weather_scheduler.get_status()
        click.echo("📊 Weather System Status:")
        click.echo(json.dumps(status_data, indent=2, default=str))
    except Exception as e:
        click.echo(f"❌ Status error: {e}")
        sys.exit(1)


async def main():
    """Main application entry point for backwards compatibility."""
    logger = get_logger("main")
    logger.info("Starting Weather Application")
    
    app = WeatherApp()
    
    if len(sys.argv) > 1:
        # Use CLI interface
        cli()
    else:
        # Default: update weather data
        success = await app.update_weather_data()
        if success:
            logger.info("Default weather update completed")
        else:
            logger.error("Default weather update failed")
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        asyncio.run(main())