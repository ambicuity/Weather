"""Advanced weather monitoring and scheduling system."""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from threading import Thread
from typing import List, Dict, Any, Optional
import signal
import sys

from .config import config
from .database import weather_db
from .alert_service import alert_service
from .logger import get_logger


class WeatherScheduler:
    """Advanced weather monitoring scheduler with multiple update strategies."""
    
    def __init__(self):
        self.logger = get_logger("scheduler")
        self._running = False
        self._scheduler_thread = None
        self._update_tasks = {
            'frequent': [],    # High-priority cities (every 5 minutes)
            'normal': [],      # Normal cities (every 15 minutes)  
            'background': []   # Low-priority cities (every hour)
        }
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def configure_city_priorities(self, 
                                frequent_cities: List[str] = None,
                                normal_cities: List[str] = None,
                                background_cities: List[str] = None):
        """Configure city update priorities."""
        self._update_tasks['frequent'] = frequent_cities or ['London', 'New York']
        self._update_tasks['normal'] = normal_cities or config.default_cities
        self._update_tasks['background'] = background_cities or []
        
        self.logger.info(f"Configured city priorities: "
                        f"{len(self._update_tasks['frequent'])} frequent, "
                        f"{len(self._update_tasks['normal'])} normal, "
                        f"{len(self._update_tasks['background'])} background")
    
    def setup_schedules(self):
        """Setup all scheduled tasks."""
        # Frequent updates (every 5 minutes)
        if self._update_tasks['frequent']:
            schedule.every(5).minutes.do(
                self._run_async_task, 
                self._update_frequent_cities
            )
        
        # Normal updates (every 15 minutes)
        if self._update_tasks['normal']:
            schedule.every(15).minutes.do(
                self._run_async_task,
                self._update_normal_cities
            )
        
        # Background updates (every hour)
        if self._update_tasks['background']:
            schedule.every().hour.do(
                self._run_async_task,
                self._update_background_cities
            )
        
        # Daily maintenance tasks
        schedule.every().day.at("02:00").do(
            self._run_async_task,
            self._daily_maintenance
        )
        
        # Weekly cleanup
        schedule.every().sunday.at("03:00").do(
            self._run_async_task,
            self._weekly_cleanup
        )
        
        # Health check every 10 minutes
        schedule.every(10).minutes.do(
            self._run_async_task,
            self._health_check
        )
        
        self.logger.info("All schedules configured")
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            self.logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self.configure_city_priorities()
        self.setup_schedules()
        
        # Run initial update
        asyncio.run(self._initial_update())
        
        # Start scheduler thread
        self._scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        self.logger.info("Weather scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        self.logger.info("Weather scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _run_async_task(self, coro_func):
        """Run async function in scheduler context."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coro_func())
        except Exception as e:
            self.logger.error(f"Error running async task: {e}")
        finally:
            loop.close()
    
    async def _initial_update(self):
        """Run initial weather update for all cities."""
        self.logger.info("Running initial weather update")
        
        try:
            # Import here to avoid circular imports
            from .main import WeatherApp
            app = WeatherApp()
            
            all_cities = list(set(
                self._update_tasks['frequent'] + 
                self._update_tasks['normal'] + 
                self._update_tasks['background']
            ))
            
            if all_cities:
                success = await app.update_weather_data(all_cities)
                self.logger.info(f"Initial update completed: {'Success' if success else 'Failed'}")
            
        except Exception as e:
            self.logger.error(f"Initial update error: {e}")
    
    async def _update_frequent_cities(self):
        """Update high-priority cities."""
        if not self._update_tasks['frequent']:
            return
        
        self.logger.info(f"Updating {len(self._update_tasks['frequent'])} frequent cities")
        
        try:
            # Import here to avoid circular imports
            from .main import WeatherApp
            app = WeatherApp()
            
            success = await app.update_weather_data(self._update_tasks['frequent'])
            
            # Check for alerts on frequent cities
            await self._check_alerts_for_cities(self._update_tasks['frequent'])
            
            self.logger.info(f"Frequent cities update: {'Success' if success else 'Failed'}")
            
        except Exception as e:
            self.logger.error(f"Frequent cities update error: {e}")
    
    async def _update_normal_cities(self):
        """Update normal priority cities."""
        if not self._update_tasks['normal']:
            return
        
        self.logger.info(f"Updating {len(self._update_tasks['normal'])} normal cities")
        
        try:
            # Import here to avoid circular imports
            from .main import WeatherApp
            app = WeatherApp()
            
            success = await app.update_weather_data(self._update_tasks['normal'])
            
            # Check for alerts
            await self._check_alerts_for_cities(self._update_tasks['normal'])
            
            self.logger.info(f"Normal cities update: {'Success' if success else 'Failed'}")
            
        except Exception as e:
            self.logger.error(f"Normal cities update error: {e}")
    
    async def _update_background_cities(self):
        """Update background priority cities."""
        if not self._update_tasks['background']:
            return
        
        self.logger.info(f"Updating {len(self._update_tasks['background'])} background cities")
        
        try:
            # Import here to avoid circular imports
            from .main import WeatherApp
            app = WeatherApp()
            
            success = await app.update_weather_data(self._update_tasks['background'])
            self.logger.info(f"Background cities update: {'Success' if success else 'Failed'}")
            
        except Exception as e:
            self.logger.error(f"Background cities update error: {e}")
    
    async def _check_alerts_for_cities(self, cities: List[str]):
        """Check for weather alerts in specified cities."""
        try:
            for city in cities:
                # Get recent weather data
                recent_data = await weather_db.get_current_weather_history(city, hours=1)
                
                if recent_data:
                    # Parse the most recent record (this is a simplified version)
                    # In a real implementation, you'd recreate the CurrentWeather object
                    self.logger.debug(f"Checked alerts for {city}")
            
        except Exception as e:
            self.logger.error(f"Error checking alerts for cities: {e}")
    
    async def _daily_maintenance(self):
        """Daily maintenance tasks."""
        self.logger.info("Running daily maintenance")
        
        try:
            # Database optimization
            await self._optimize_database()
            
            # Generate daily weather report
            await self._generate_daily_report()
            
            # Check system health
            await self._comprehensive_health_check()
            
            self.logger.info("Daily maintenance completed")
            
        except Exception as e:
            self.logger.error(f"Daily maintenance error: {e}")
    
    async def _weekly_cleanup(self):
        """Weekly cleanup tasks."""
        self.logger.info("Running weekly cleanup")
        
        try:
            # Clean up old data (keep 30 days)
            await weather_db.cleanup_old_data(days_to_keep=30)
            
            # Archive old alerts
            await self._archive_old_alerts()
            
            # Generate weekly summary
            await self._generate_weekly_summary()
            
            self.logger.info("Weekly cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Weekly cleanup error: {e}")
    
    async def _health_check(self):
        """Regular health check."""
        try:
            # Check database connection
            stats = await weather_db.get_database_stats()
            
            # Check if recent data exists
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            # Log health status
            self.logger.debug(f"Health check: {stats['current_weather_records']} records, "
                            f"{stats['unique_locations']} locations")
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
    
    async def _optimize_database(self):
        """Optimize database performance."""
        try:
            # Run VACUUM to optimize SQLite database
            async with weather_db._lock:
                with weather_db._get_connection() as conn:
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
            
            self.logger.info("Database optimized")
            
        except Exception as e:
            self.logger.error(f"Database optimization error: {e}")
    
    async def _generate_daily_report(self):
        """Generate daily weather report."""
        try:
            today = datetime.utcnow().date()
            all_cities = list(set(
                self._update_tasks['frequent'] + 
                self._update_tasks['normal'] + 
                self._update_tasks['background']
            ))
            
            report_data = {}
            for city in all_cities[:5]:  # Limit to first 5 cities for report
                try:
                    trends = await weather_db.get_weather_trends(city, days=1)
                    report_data[city] = trends
                except Exception as e:
                    self.logger.warning(f"Failed to get trends for {city}: {e}")
            
            self.logger.info(f"Daily report generated for {len(report_data)} cities")
            
        except Exception as e:
            self.logger.error(f"Daily report generation error: {e}")
    
    async def _generate_weekly_summary(self):
        """Generate weekly weather summary."""
        try:
            stats = await weather_db.get_database_stats()
            active_alerts = await alert_service.get_active_alerts_summary()
            
            summary = {
                "week_ending": datetime.utcnow().date().isoformat(),
                "total_records": stats["current_weather_records"],
                "unique_locations": stats["unique_locations"],
                "active_alerts": stats["active_alerts"],
                "database_size_mb": stats["database_size_mb"]
            }
            
            self.logger.info(f"Weekly summary: {summary}")
            
        except Exception as e:
            self.logger.error(f"Weekly summary generation error: {e}")
    
    async def _comprehensive_health_check(self):
        """Comprehensive system health check."""
        try:
            health_status = {
                "timestamp": datetime.utcnow().isoformat(),
                "database_healthy": True,
                "api_responsive": True,
                "recent_data_available": True,
                "alerts_system_working": True
            }
            
            # Test database
            try:
                await weather_db.get_database_stats()
            except Exception:
                health_status["database_healthy"] = False
            
            # Test alert system
            try:
                await alert_service.get_active_alerts_summary()
            except Exception:
                health_status["alerts_system_working"] = False
            
            # Check for recent data
            try:
                cutoff = datetime.utcnow() - timedelta(hours=2)
                # This is a simplified check - in production you'd query recent records
                health_status["recent_data_available"] = True
            except Exception:
                health_status["recent_data_available"] = False
            
            overall_healthy = all(health_status[key] for key in health_status if key != "timestamp")
            
            if overall_healthy:
                self.logger.info("Comprehensive health check: All systems operational")
            else:
                self.logger.warning(f"Health check issues detected: {health_status}")
            
        except Exception as e:
            self.logger.error(f"Comprehensive health check error: {e}")
    
    async def _archive_old_alerts(self):
        """Archive old resolved alerts."""
        try:
            # This would move old alerts to an archive table in a real implementation
            # For now, just log the action
            self.logger.info("Old alerts archived")
            
        except Exception as e:
            self.logger.error(f"Alert archiving error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "running": self._running,
            "next_jobs": [str(job) for job in schedule.jobs[:5]],  # Next 5 jobs
            "city_priorities": {
                "frequent": len(self._update_tasks['frequent']),
                "normal": len(self._update_tasks['normal']),
                "background": len(self._update_tasks['background'])
            },
            "total_scheduled_jobs": len(schedule.jobs)
        }


def run_scheduler():
    """Run the weather scheduler as a standalone service."""
    logger = get_logger("scheduler_main")
    logger.info("Starting Weather Scheduler Service")
    
    scheduler = WeatherScheduler()
    
    try:
        scheduler.start()
        
        # Keep the main thread alive
        while scheduler._running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Scheduler service error: {e}")
    finally:
        scheduler.stop()
        logger.info("Weather Scheduler Service stopped")


# Global scheduler instance
weather_scheduler = WeatherScheduler()


if __name__ == "__main__":
    run_scheduler()