"""Main weather application."""

import asyncio
import sys
from datetime import datetime
from typing import List

from .config import config
from .weather_service import weather_service
from .database import weather_db
from .logger import get_logger


class WeatherApp:
    """Main weather application."""
    
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
            
            # Store successful results in database
            for location, weather in weather_data.items():
                if weather:
                    await weather_db.store_current_weather(weather)
            
            self.logger.info(f"Weather update completed: {result.locations_updated}")
            
            # Generate updated CSV and README
            await self._update_output_files(weather_data)
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"Error during weather update: {e}")
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
        """Update README.md with weather table."""
        try:
            # Read current README
            with open("README.md", "r", encoding="utf-8") as f:
                content = f.read()
            
            # Build weather table
            table_rows = ["<table><tr><th>City</th><th>Temperature (°C)</th><th>Condition</th><th>Humidity (%)</th><th>Wind (km/h)</th><th>Last Updated</th></tr>"]
            
            for location, weather in weather_data.items():
                if weather:
                    last_updated = weather.last_updated.strftime("%Y-%m-%d %H:%M")
                    table_rows.append(f"<tr><td>{weather.location.name}</td><td>{weather.temperature_c}</td><td>{weather.condition}</td><td>{weather.humidity}</td><td>{weather.wind_speed_kph}</td><td>{last_updated}</td></tr>")
            
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
                
                self.logger.info("Updated README.md with weather data")
            
        except Exception as e:
            self.logger.error(f"Error updating README: {e}")
    
    async def get_weather_summary(self) -> dict:
        """Get a summary of current weather status."""
        try:
            db_stats = await weather_db.get_database_stats()
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "database_stats": db_stats,
                "configured_locations": len(config.default_cities),
                "default_cities": config.default_cities
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting weather summary: {e}")
            return {"error": str(e)}


async def main():
    """Main application entry point."""
    logger = get_logger("main")
    logger.info("Starting Weather Application")
    
    app = WeatherApp()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "update":
            # Update weather data
            locations = sys.argv[2:] if len(sys.argv) > 2 else None
            success = await app.update_weather_data(locations)
            if success:
                logger.info("Weather update completed successfully")
                sys.exit(0)
            else:
                logger.error("Weather update failed")
                sys.exit(1)
        
        elif command == "summary":
            # Show weather summary
            summary = await app.get_weather_summary()
            print(f"Weather App Summary: {summary}")
        
        elif command == "cleanup":
            # Cleanup old data
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            await weather_db.cleanup_old_data(days)
            logger.info(f"Cleanup completed for data older than {days} days")
        
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)
    
    else:
        # Default: update weather data
        success = await app.update_weather_data()
        if success:
            logger.info("Default weather update completed")
        else:
            logger.error("Default weather update failed")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())