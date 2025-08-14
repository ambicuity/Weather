# Weather Updates - Production-Level Weather Monitoring System

🌤️ **A comprehensive, production-ready weather monitoring and forecasting system with advanced features, real-time alerts, and enterprise-grade architecture.**

<!-- WEATHER-UPDATE-START -->
<table><tr><th>City</th><th>Temperature (°C)</th><th>Condition</th><th>Humidity (%)</th><th>Wind (km/h)</th><th>Last Updated</th></tr></table>
<!-- WEATHER-UPDATE-END -->

## 🚀 Features

### Core Weather Monitoring
- **Real-time Weather Data**: Current conditions for multiple cities worldwide
- **Extended Forecasting**: 5-30 day forecasts with prediction models
- **Hourly Forecasts**: Detailed hourly weather breakdown
- **Historical Data**: Complete weather history with trend analysis
- **Weather Alerts**: Configurable thresholds and automated notifications

### Advanced Analytics
- **Weather Pattern Detection**: Automatic identification of significant weather changes
- **Trend Analysis**: Historical weather trends and seasonal patterns  
- **Prediction Models**: Multiple forecasting algorithms (linear, moving average, weighted)
- **Change Detection**: Alerts for temperature swings, storm systems, and pressure changes

### Production Features
- **RESTful API**: Comprehensive API with 15+ endpoints
- **Web Dashboard**: Real-time weather visualization
- **Database Integration**: SQLite/PostgreSQL with historical data storage
- **Caching Layer**: Redis integration for performance optimization
- **Rate Limiting**: API throttling and abuse prevention
- **Monitoring & Alerting**: System health checks and email notifications

### Enterprise Architecture
- **Microservices Design**: Modular, scalable architecture
- **Docker Deployment**: Container-based deployment with orchestration
- **Load Balancing**: Nginx reverse proxy with SSL termination  
- **Automated Scheduling**: Intelligent update scheduling with priority levels
- **Logging & Monitoring**: Comprehensive logging with log rotation
- **Backup System**: Automated database backups and disaster recovery

## 📋 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Weather API key from [WeatherAPI.com](https://weatherapi.com)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ambicuity/Weather.git
cd Weather
```

2. **Run the setup script:**
```bash
python setup.py
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API key and settings
```

4. **Start the application:**
```bash
# Development mode
python -m src.main update

# Production mode with Docker
docker-compose up -d
```

## 🛠️ Usage

### Command Line Interface

```bash
# Update weather data
python -m src.main update --locations London,Paris,Tokyo

# Get comprehensive forecast
python -m src.main forecast --location London --days 10

# Setup weather monitoring
python -m src.main monitor --location London --temp-high 30 --temp-low 5

# Start API server
python -m src.main serve --host 0.0.0.0 --port 5000

# Run scheduler service
python -m src.main scheduler

# View system status
python -m src.main status

# Get weather summary
python -m src.main summary
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/weather/{location}` | GET | Current weather |
| `/api/forecast/{location}` | GET | Weather forecast |
| `/api/forecast/{location}/extended` | GET | Extended forecast with predictions |
| `/api/forecast/{location}/hourly` | GET | Hourly forecast |
| `/api/weather/{location}/history` | GET | Weather history |
| `/api/weather/{location}/trends` | GET | Weather trend analysis |
| `/api/weather/{location}/changes` | GET | Detected weather changes |
| `/api/alerts` | GET | Active weather alerts |
| `/api/alerts/setup` | POST | Configure alert thresholds |
| `/api/weather/bulk` | GET | Multi-location weather |
| `/api/stats` | GET | System statistics |

### Web Dashboard

Access the interactive dashboard at `http://localhost:8080/dashboard`

Features:
- Real-time weather display
- Search for any location
- Weather alerts visualization
- System statistics
- Auto-refresh every 5 minutes
- Mobile-responsive design

## 🏗️ Architecture

The system follows a microservices architecture with the following components:

- **Weather Service**: Core API integration and data fetching
- **Forecast Service**: Advanced forecasting and prediction models
- **Alert Service**: Weather monitoring and notification system
- **Database Service**: Historical data storage and analytics
- **API Service**: RESTful web API with comprehensive endpoints
- **Scheduler Service**: Automated background tasks and monitoring
- **Web Dashboard**: Interactive user interface

## 🐳 Production Deployment

### Docker Deployment

```bash
# Build and deploy with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale weather-api=3

# View logs
docker-compose logs -f weather-api
```

### Full Production Deployment

```bash
# Run the production deployment script (Ubuntu/Debian)
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

This sets up:
- System dependencies and Docker
- Service user and directories
- Nginx reverse proxy with SSL
- Systemd services
- Automated monitoring and backups
- Log rotation and firewall
- Health checks and alerting

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WEATHER_API_KEY` | WeatherAPI.com API key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///weather.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `UPDATE_INTERVAL_MINUTES` | Update frequency | `5` |
| `DEFAULT_CITIES` | Default cities to monitor | `London,New York,Tokyo...` |

### Weather Monitoring

```bash
# Setup temperature monitoring
python -m src.main monitor \
  --location "London" \
  --temp-high 30 \
  --temp-low 5 \
  --wind-speed 50 \
  --humidity 90
```

## 📊 Monitoring & Alerting

### System Monitoring

- **Health Checks**: Automated system health monitoring
- **Performance Metrics**: API response times, database performance
- **Resource Usage**: CPU, memory, disk space monitoring
- **Log Analysis**: Error tracking and performance analysis

### Weather Alerts

Configure custom thresholds for:
- Temperature extremes
- High wind speeds  
- Humidity levels
- UV index warnings
- Pressure changes
- Visibility conditions

## 🧪 Testing

```bash
# Run basic functionality tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [WeatherAPI.com](https://weatherapi.com) for providing weather data
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- [Rich](https://rich.readthedocs.io/) for beautiful console output

---

**Built with ❤️ for production-level weather monitoring**
