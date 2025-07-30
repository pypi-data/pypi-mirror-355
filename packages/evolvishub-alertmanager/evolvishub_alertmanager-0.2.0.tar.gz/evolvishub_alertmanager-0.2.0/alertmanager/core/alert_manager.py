"""
AlertManager class for managing alerts in the system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from .base_manager import BaseManager
from .sqlite_adapter import SQLiteAdapter
from ..config.config_manager import ConfigManager

class AlertManager(BaseManager):
    """Manager class for handling alerts in the system."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the AlertManager.

        Args:
            config_path (str, optional): Path to configuration file
        """
        config = ConfigManager(config_path)
        db_config = config.get_database_config()
        
        db = SQLiteAdapter(
            database_path=db_config['path'],
            pool_size=db_config.get('pool_size', 5),
            max_overflow=db_config.get('max_overflow', 10)
        )
        
        super().__init__(
            db=db,
            table_name='alerts',
            migration_file='migrations/create_alerts_table.sql'
        )
        
        self.config = config

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get schema information for the alerts table.

        Returns:
            Dict[str, Any]: Schema information
        """
        return {
            'table_name': 'alerts',
            'columns': {
                'id': {'type': 'INTEGER', 'primary_key': True},
                'alert_type': {'type': 'TEXT', 'required': True},
                'message': {'type': 'TEXT', 'required': True},
                'severity': {'type': 'TEXT', 'required': True},
                'status': {'type': 'TEXT', 'required': True},
                'source': {'type': 'TEXT', 'required': True},
                'acknowledged_by': {'type': 'TEXT'},
                'acknowledged_at': {'type': 'DATETIME'},
                'resolved_by': {'type': 'TEXT'},
                'resolved_at': {'type': 'DATETIME'},
                'metadata': {'type': 'TEXT', 'json': True},
                'created_at_evie': {'type': 'DATETIME', 'required': True},
                'updated_at_evie': {'type': 'DATETIME', 'required': True}
            }
        }

    def create_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = 'info',
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a new alert with simplified interface (for backward compatibility).

        Args:
            alert_type (str): Type of alert
            message (str): Alert message
            severity (str): Severity level
            source (str, optional): Source of the alert
            metadata (dict, optional): Additional metadata

        Returns:
            int: ID of the created alert
        """
        alert_config = self.config.get_alert_config()

        data = {
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'status': 'active',
            'source': source or alert_config.get('default_source', 'system'),
            'metadata': metadata or {}
        }

        return self.create_record(data)

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id (int): ID of the alert to acknowledge
            acknowledged_by (str): User who acknowledged the alert

        Returns:
            bool: True if successful
        """
        return self.update_record(alert_id, {
            'status': 'acknowledged',
            'acknowledged_by': acknowledged_by,
            'acknowledged_at': datetime.now()
        })

    def resolve_alert(self, alert_id: int, resolved_by: Optional[str] = None) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id (int): ID of the alert to resolve
            resolved_by (str, optional): User who resolved the alert

        Returns:
            bool: True if successful
        """
        update_data = {
            'status': 'resolved',
            'resolved_at': datetime.now()
        }
        if resolved_by:
            update_data['resolved_by'] = resolved_by

        return self.update_record(alert_id, update_data)

    def get_alerts(
        self,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get alerts with optional filtering.

        Args:
            alert_type (str, optional): Filter by alert type
            severity (str, optional): Filter by severity
            status (str, optional): Filter by status
            limit (int, optional): Maximum number of alerts to return
            offset (int): Number of alerts to skip

        Returns:
            List[Dict[str, Any]]: List of alerts
        """
        filters = {}
        if alert_type:
            filters['alert_type'] = alert_type
        if severity:
            filters['severity'] = severity
        if status:
            filters['status'] = status

        return self.get_records(filters=filters if filters else None, limit=limit, offset=offset)

    def get_active_alerts_count(self) -> Dict[str, int]:
        """
        Get count of active alerts by severity.

        Returns:
            Dict[str, int]: Count of active alerts by severity
        """
        query = """
            SELECT severity, COUNT(*) as count
            FROM alerts
            WHERE status = 'active'
            GROUP BY severity
        """
        results = self.db.execute_query(query)
        return {row['severity']: row['count'] for row in results}

    def delete_old_alerts(self, days: Optional[int] = None) -> int:
        """
        Delete alerts older than specified days.

        Args:
            days (int, optional): Number of days to keep alerts

        Returns:
            int: Number of alerts deleted
        """
        if days is None:
            days = self.config.get_alert_config()['retention_days']
        return self.delete_old_records(days=days)

    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about alerts.

        Returns:
            Dict[str, Any]: Alert statistics
        """
        stats = {
            'by_status': {},
            'by_severity': {},
            'by_type': {},
            'avg_resolution_days': 0
        }
        
        # Get counts by status
        status_query = """
            SELECT status, COUNT(*) as count
            FROM alerts
            GROUP BY status
        """
        results = self.db.execute_query(status_query)
        stats['by_status'] = {row['status']: row['count'] for row in results}
        
        # Get counts by severity
        severity_query = """
            SELECT severity, COUNT(*) as count
            FROM alerts
            GROUP BY severity
        """
        results = self.db.execute_query(severity_query)
        stats['by_severity'] = {row['severity']: row['count'] for row in results}

        # Get counts by type
        type_query = """
            SELECT alert_type, COUNT(*) as count
            FROM alerts
            GROUP BY alert_type
        """
        results = self.db.execute_query(type_query)
        stats['by_type'] = {row['alert_type']: row['count'] for row in results}

        # Calculate average resolution time
        resolution_query = """
            SELECT AVG(julianday(resolved_at) - julianday(created_at_evie)) as avg_days
            FROM alerts
            WHERE resolved_at IS NOT NULL
        """
        result = self.db.execute_query(resolution_query)
        stats['avg_resolution_days'] = result[0]['avg_days'] if result else 0
        
        return stats

    def get_alert_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get alert trends over time.

        Args:
            days (int): Number of days to analyze

        Returns:
            Dict[str, Any]: Alert trends
        """
        trends = {
            'daily': {},
            'resolution_time': {}
        }
        
        # Get daily alert counts
        daily_query = """
            SELECT date(created_at_evie) as date, COUNT(*) as count
            FROM alerts
            WHERE created_at_evie >= date('now', ?)
            GROUP BY date(created_at_evie)
            ORDER BY date
        """
        results = self.db.execute_query(daily_query, (f'-{days} days',))
        trends['daily'] = {row['date']: row['count'] for row in results}
        
        # Get resolution time trends
        resolution_query = """
            SELECT date(resolved_at) as date, AVG(julianday(resolved_at) - julianday(created_at_evie)) as avg_days
            FROM alerts
            WHERE resolved_at IS NOT NULL
            AND resolved_at >= date('now', ?)
            GROUP BY date(resolved_at)
            ORDER BY date
        """
        results = self.db.execute_query(resolution_query, (f'-{days} days',))
        trends['resolution_time'] = {row['date']: row['avg_days'] for row in results}
        
        return trends

    def get_source_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics about alert sources.

        Returns:
            Dict[str, Dict[str, int]]: Statistics by source
        """
        # Get counts by source and severity
        query = """
            SELECT source, severity, COUNT(*) as count
            FROM alerts
            GROUP BY source, severity
        """
        results = self.db.execute_query(query)

        stats = {}
        for row in results:
            if row['source'] not in stats:
                stats[row['source']] = {}
            stats[row['source']][row['severity']] = row['count']

        # Get total counts by source
        total_query = """
            SELECT source, COUNT(*) as count
            FROM alerts
            GROUP BY source
        """
        total_results = self.db.execute_query(total_query)

        for row in total_results:
            if row['source'] not in stats:
                stats[row['source']] = {}
            stats[row['source']]['total'] = row['count']

        return stats

    def get_alert_metrics(self, time_period: str = '24h') -> Dict[str, Any]:
        """
        Get key performance metrics for alerts.

        Args:
            time_period (str): Time period to analyze (e.g., '24h', '7d', '30d')

        Returns:
            Dict[str, Any]: Alert metrics
        """
        metrics = {
            'total_alerts': 0,
            'resolution_rate': 0,
            'critical_percentage': 0
        }
        
        # Convert time period to SQLite interval
        interval_map = {
            '24h': '1 day',
            '7d': '7 days',
            '30d': '30 days'
        }
        interval = interval_map.get(time_period, '1 day')
        
        # Get total alerts
        total_query = f"""
            SELECT COUNT(*) as count
            FROM alerts
            WHERE created_at_evie >= datetime('now', '-{interval}')
        """
        result = self.db.execute_query(total_query)
        metrics['total_alerts'] = result[0]['count'] if result else 0
        
        # Get resolution rate
        resolution_query = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved
            FROM alerts
            WHERE created_at_evie >= datetime('now', '-{interval}')
        """
        result = self.db.execute_query(resolution_query)
        if result and result[0]['total'] > 0:
            metrics['resolution_rate'] = (result[0]['resolved'] / result[0]['total']) * 100
        
        # Get critical alerts percentage
        critical_query = f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical
            FROM alerts
            WHERE created_at_evie >= datetime('now', '-{interval}')
        """
        result = self.db.execute_query(critical_query)
        if result and result[0]['total'] > 0:
            metrics['critical_percentage'] = (result[0]['critical'] / result[0]['total']) * 100
        
        return metrics

    def query_alerts(
        self,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generic query function for alerts table.

        Args:
            columns (List[str], optional): Columns to select. Defaults to all.
            filters (Dict[str, Any], optional): WHERE clause filters.
            order_by (str, optional): Column to order by.
            limit (int, optional): Limit number of results.
            offset (int, optional): Offset for results.

        Returns:
            List[Dict[str, Any]]: List of alert records.
        """
        return self.query_records(
            columns=columns,
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset
        )