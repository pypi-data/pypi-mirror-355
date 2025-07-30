# AlertManager

<div align="center">
  <img src="assets/png/eviesales.png" alt="Evolvis Logo" width="200"/>
</div>

A flexible alert management system with SQLite backend that can be used as a library in Python applications.

## About

AlertManager is developed by [Evolvis](https://evolvis.ai), a company specializing in intelligent automation and monitoring solutions. This library provides a robust foundation for managing alerts in any Python application, with a focus on flexibility, performance, and ease of use.

## Author

**Alban Maxhuni, PhD**  
Email: a.maxhuni@evolvis.ai

## Features

- SQLite-based alert storage
- Configurable through YAML or INI files
- Support for different alert types and severities
- Alert acknowledgment and resolution tracking
- Metadata support for additional information
- Automatic cleanup of old alerts
- Configurable logging with enable/disable option
- Advanced statistics and metrics
- Trend analysis and reporting

## Installation

```bash
pip install alertmanager
```

## Usage

### Basic Usage

```python
from alertmanager import AlertManager

# Initialize with default configuration
alert_manager = AlertManager()

# Create an alert
alert_id = alert_manager.create_alert(
    title="Disk space is running low",
    description="Disk usage is above 85%",
    severity="warning"
)

# Get active alerts
alerts = alert_manager.get_alerts(status="active")

# Acknowledge an alert
alert_manager.acknowledge_alert(alert_id, "admin")

# Resolve an alert
alert_manager.resolve_alert(alert_id, "admin")
```

### Advanced Usage

```python
# Get comprehensive statistics
stats = alert_manager.get_alert_statistics()
print(f"Total alerts by status: {stats['by_status']}")
print(f"Alerts by severity: {stats['by_severity']}")
print(f"Average resolution time: {stats['avg_resolution_days']} days")

# Get alert trends
trends = alert_manager.get_alert_trends(days=30)
print(f"Daily alert counts: {trends['daily']}")
print(f"Resolution time trends: {trends['resolution_time']}")

# Get source statistics
source_stats = alert_manager.get_source_statistics()
print(f"Statistics by source: {source_stats}")

# Get key performance metrics
metrics = alert_manager.get_alert_metrics(time_period='24h')
print(f"Total alerts in last 24h: {metrics['total_alerts']}")
print(f"Resolution rate: {metrics['resolution_rate']}%")
print(f"Critical alerts percentage: {metrics['critical_percentage']}%")
```

### Configuration

AlertManager requires a configuration file to be provided by the application that uses it. You can use either YAML or INI format. The library includes a default configuration template that you can use as a starting point.

#### Configuration File Location

The configuration file should be placed in your application's configuration directory. By default, AlertManager will look for:
- `config.yaml` or `config.yml`
- `config.ini`

in the current working directory. You can also specify a custom path when initializing AlertManager:

```python
alert_manager = AlertManager(config_path="/path/to/your/config.yaml")
```

#### Configuration Template

Here's an example configuration file (`config.yaml`):

```yaml
database:
  # Path to SQLite database file (use ":memory:" for in-memory database)
  path: alertmanager.sql
  # Directory containing database migrations
  migrations_dir: migrations
  # Connection pool settings
  pool_size: 5
  max_overflow: 10
  # Enable SQL query logging (for debugging)
  echo: false

logging:
  # Enable or disable logging
  enabled: true
  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  level: INFO
  # Log message format
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  # Log file path
  file: alertmanager.log

alerts:
  # Number of days to keep alerts before automatic deletion
  retention_days: 30
  # Default severity for new alerts if not specified
  default_severity: info
  # Default source for new alerts if not specified
  default_source: system
  # Maximum number of alerts to return in a single query
  max_alerts_per_page: 100
```

Or using INI format (`config.ini`):

```ini
[database]
path = alertmanager.sql
migrations_dir = migrations
pool_size = 5
max_overflow = 10
echo = false

[logging]
enabled = true
level = INFO
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
file = alertmanager.log

[alerts]
retention_days = 30
default_severity = info
default_source = system
max_alerts_per_page = 100
```

#### Configuration Options

| Section | Option | Description | Default |
|---------|--------|-------------|---------|
| database | path | Path to SQLite database file | alertmanager.sql |
| database | migrations_dir | Directory containing migrations | migrations |
| database | pool_size | Connection pool size | 5 |
| database | max_overflow | Maximum overflow connections | 10 |
| database | echo | Enable SQL query logging | false |
| logging | enabled | Enable or disable logging | true |
| logging | level | Logging level | INFO |
| logging | format | Log message format | '%(asctime)s - %(name)s - %(levelname)s - %(message)s' |
| logging | file | Log file path | alertmanager.log |
| alerts | retention_days | Days to keep alerts | 30 |
| alerts | default_severity | Default alert severity | info |
| alerts | default_source | Default alert source | system |
| alerts | max_alerts_per_page | Max alerts per query | 100 |

## API Reference

### AlertManager

#### Core Methods

- `create_alert(title, description, severity=None)`: Create a new alert
- `get_alerts(status=None, limit=None, offset=0)`: Get alerts with optional filtering
- `acknowledge_alert(alert_id, acknowledged_by)`: Acknowledge an alert
- `resolve_alert(alert_id, resolved_by)`: Resolve an alert
- `get_active_alerts_count()`: Get count of active alerts by severity
- `delete_old_alerts(days=None)`: Delete alerts older than specified days
- `query_alerts(columns=None, filters=None, order_by=None, limit=None, offset=None)`: Generic query function

#### Statistical Methods

- `get_alert_statistics()`: Get comprehensive statistics about alerts
- `get_alert_trends(days=30)`: Get alert trends over time
- `get_source_statistics()`: Get statistics about alert sources
- `get_alert_metrics(time_period='24h')`: Get key performance metrics for alerts

## License

MIT License