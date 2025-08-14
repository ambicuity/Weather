#!/bin/bash

# Weather Application Deployment Script
# Production-ready deployment with monitoring and backup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/weather-app"
BACKUP_DIR="/opt/weather-backup"
SERVICE_USER="weather"
LOG_FILE="/var/log/weather-deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    apt-get update
    apt-get install -y \
        docker.io \
        docker-compose \
        nginx \
        python3 \
        python3-pip \
        sqlite3 \
        curl \
        wget \
        git \
        cron \
        logrotate \
        fail2ban \
        ufw
    
    # Enable Docker
    systemctl enable docker
    systemctl start docker
    
    success "System dependencies installed"
}

# Create service user
create_user() {
    log "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir "$DEPLOY_DIR" --create-home "$SERVICE_USER"
        usermod -aG docker "$SERVICE_USER"
        success "Service user created"
    else
        log "Service user already exists"
    fi
}

# Setup directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p /var/log/weather
    mkdir -p /etc/weather
    
    # Set permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DEPLOY_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$BACKUP_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/weather
    
    success "Directories created"
}

# Deploy application
deploy_application() {
    log "Deploying Weather Application..."
    
    # Stop existing services
    cd "$DEPLOY_DIR"
    if [[ -f docker-compose.yml ]]; then
        docker-compose down || true
    fi
    
    # Backup existing data
    if [[ -d data ]]; then
        backup_name="weather-backup-$(date +%Y%m%d-%H%M%S)"
        cp -r data "$BACKUP_DIR/$backup_name"
        log "Backed up existing data to $BACKUP_DIR/$backup_name"
    fi
    
    # Copy application files
    cp -r /home/runner/work/Weather/Weather/* "$DEPLOY_DIR/"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DEPLOY_DIR"
    
    success "Application deployed"
}

# Configure environment
configure_environment() {
    log "Configuring environment..."
    
    # Create production environment file
    cat > "$DEPLOY_DIR/.env" << EOF
# Production Weather Application Configuration
WEATHER_API_KEY=\${WEATHER_API_KEY:-your_weather_api_key_here}
WEATHER_API_BASE_URL=http://api.weatherapi.com/v1

# Database Configuration
DATABASE_URL=sqlite:///data/weather.db
REDIS_URL=redis://localhost:6379/0

# Email Configuration (configure with your SMTP settings)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
NOTIFICATION_EMAIL_TO=

# Application Configuration
LOG_LEVEL=INFO
UPDATE_INTERVAL_MINUTES=5
CACHE_TTL_SECONDS=300
MAX_RETRIES=3
REQUEST_TIMEOUT_SECONDS=30

# Cities Configuration
DEFAULT_CITIES=London,New York,Tokyo,Paris,Sydney,Mumbai,Beijing,São Paulo,Lagos,Moscow
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" "$DEPLOY_DIR/.env"
    chmod 600 "$DEPLOY_DIR/.env"
    
    success "Environment configured"
}

# Setup systemd services
setup_services() {
    log "Setting up systemd services..."
    
    # Weather API service
    cat > /etc/systemd/system/weather-api.service << EOF
[Unit]
Description=Weather API Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/local/bin/docker-compose up weather-api
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Weather Scheduler service
    cat > /etc/systemd/system/weather-scheduler.service << EOF
[Unit]
Description=Weather Scheduler Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/local/bin/docker-compose up weather-scheduler
ExecStop=/usr/local/bin/docker-compose down
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    success "Systemd services configured"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring script
    cat > "$DEPLOY_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# Weather Application Monitoring Script

DEPLOY_DIR="/opt/weather-app"
LOG_FILE="/var/log/weather/monitor.log"

cd "$DEPLOY_DIR"

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "$(date): Weather services are down, restarting..." >> "$LOG_FILE"
    docker-compose up -d
fi

# Check API health
if ! curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "$(date): Weather API health check failed" >> "$LOG_FILE"
    docker-compose restart weather-api
fi

# Check disk space
DISK_USAGE=$(df -h "$DEPLOY_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): High disk usage: ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Clean old logs
find /var/log/weather -name "*.log" -mtime +30 -delete
EOF
    
    chmod +x "$DEPLOY_DIR/monitor.sh"
    
    # Add to crontab
    (crontab -u "$SERVICE_USER" -l 2>/dev/null; echo "*/5 * * * * $DEPLOY_DIR/monitor.sh") | crontab -u "$SERVICE_USER" -
    
    success "Monitoring configured"
}

# Setup log rotation
setup_logrotate() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/weather << EOF
/var/log/weather/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload weather-api weather-scheduler 2>/dev/null || true
    endscript
}
EOF
    
    success "Log rotation configured"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow weather API port
    ufw allow 5000/tcp
    ufw allow 8080/tcp
    
    # Enable firewall
    ufw --force enable
    
    success "Firewall configured"
}

# Setup backup
setup_backup() {
    log "Setting up backup system..."
    
    cat > "$DEPLOY_DIR/backup.sh" << 'EOF'
#!/bin/bash
# Weather Application Backup Script

DEPLOY_DIR="/opt/weather-app"
BACKUP_DIR="/opt/weather-backup"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/weekly"

# Backup database
if [[ -f "$DEPLOY_DIR/data/weather.db" ]]; then
    cp "$DEPLOY_DIR/data/weather.db" "$BACKUP_DIR/daily/weather-${TIMESTAMP}.db"
    
    # Weekly backup on Sundays
    if [[ $(date +%u) -eq 7 ]]; then
        cp "$DEPLOY_DIR/data/weather.db" "$BACKUP_DIR/weekly/weather-${TIMESTAMP}.db"
    fi
fi

# Backup configuration
cp "$DEPLOY_DIR/.env" "$BACKUP_DIR/daily/env-${TIMESTAMP}"

# Clean old daily backups (keep 7 days)
find "$BACKUP_DIR/daily" -name "weather-*.db" -mtime +7 -delete
find "$BACKUP_DIR/daily" -name "env-*" -mtime +7 -delete

# Clean old weekly backups (keep 8 weeks)
find "$BACKUP_DIR/weekly" -name "weather-*.db" -mtime +56 -delete

echo "$(date): Backup completed" >> /var/log/weather/backup.log
EOF
    
    chmod +x "$DEPLOY_DIR/backup.sh"
    
    # Add to crontab (daily at 2 AM)
    (crontab -u "$SERVICE_USER" -l 2>/dev/null; echo "0 2 * * * $DEPLOY_DIR/backup.sh") | crontab -u "$SERVICE_USER" -
    
    success "Backup system configured"
}

# Start services
start_services() {
    log "Starting Weather Application services..."
    
    cd "$DEPLOY_DIR"
    
    # Build and start with docker-compose
    sudo -u "$SERVICE_USER" docker-compose up -d --build
    
    # Wait for services to be ready
    sleep 30
    
    # Check if services are running
    if sudo -u "$SERVICE_USER" docker-compose ps | grep -q "Up"; then
        success "Weather Application services started successfully"
    else
        error "Failed to start Weather Application services"
    fi
}

# Main deployment function
main() {
    log "Starting Weather Application Production Deployment"
    
    check_root
    install_dependencies
    create_user
    setup_directories
    deploy_application
    configure_environment
    setup_services
    setup_monitoring
    setup_logrotate
    setup_firewall
    setup_backup
    start_services
    
    success "Weather Application deployed successfully!"
    
    echo ""
    echo "🌤️  Weather Application Production Deployment Complete!"
    echo ""
    echo "Services:"
    echo "  - Weather API: http://localhost:5000"
    echo "  - Weather Dashboard: http://localhost:8080"
    echo "  - API Documentation: http://localhost:5000/"
    echo ""
    echo "Management Commands:"
    echo "  - View logs: journalctl -u weather-api -f"
    echo "  - Check status: systemctl status weather-api weather-scheduler"
    echo "  - Restart services: systemctl restart weather-api weather-scheduler"
    echo ""
    echo "Configuration:"
    echo "  - Edit $DEPLOY_DIR/.env to configure API keys and settings"
    echo "  - Backup location: $BACKUP_DIR"
    echo "  - Logs location: /var/log/weather"
    echo ""
    echo "Next steps:"
    echo "  1. Configure your weather API key in $DEPLOY_DIR/.env"
    echo "  2. Setup SSL certificates for HTTPS (recommended)"
    echo "  3. Configure email notifications"
    echo "  4. Setup monitoring alerts"
}

# Run deployment
main "$@"