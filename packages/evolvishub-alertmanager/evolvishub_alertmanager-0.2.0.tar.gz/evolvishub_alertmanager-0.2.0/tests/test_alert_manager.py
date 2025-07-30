import os
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from alertmanager import AlertManager

@pytest.fixture
def alert_manager():
    """Create an AlertManager instance for testing."""
    config_path = Path(__file__).parent / "test_config.yaml"
    manager = AlertManager(config_path=str(config_path))
    return manager

def test_create_alert(alert_manager):
    """Test creating a new alert."""
    alert_id = alert_manager.create_alert(
        alert_type="test",
        message="Test alert",
        severity="info",
        metadata={"test_key": "test_value"}
    )
    assert alert_id is not None
    
    # Verify alert was created
    alerts = alert_manager.get_alerts(alert_type="test")
    assert len(alerts) == 1
    assert alerts[0]["message"] == "Test alert"
    assert alerts[0]["severity"] == "info"
    assert alerts[0]["source"] == "system"  # Default source
    assert alerts[0]["metadata"]["test_key"] == "test_value"

def test_get_alerts(alert_manager):
    """Test getting alerts with various filters."""
    # Create test alerts
    alert_manager.create_alert("type1", "Alert 1", "info")
    alert_manager.create_alert("type1", "Alert 2", "warning")
    alert_manager.create_alert("type2", "Alert 3", "error")
    
    # Test filtering by type
    alerts = alert_manager.get_alerts(alert_type="type1")
    assert len(alerts) == 2
    
    # Test filtering by severity
    alerts = alert_manager.get_alerts(severity="error")
    assert len(alerts) == 1
    assert alerts[0]["message"] == "Alert 3"
    
    # Test limit and offset
    alerts = alert_manager.get_alerts(limit=2, offset=1)
    assert len(alerts) == 2

def test_acknowledge_alert(alert_manager):
    """Test acknowledging an alert."""
    alert_id = alert_manager.create_alert("test", "Test alert")
    
    # Acknowledge alert
    assert alert_manager.acknowledge_alert(alert_id, "test_user")
    
    # Verify status
    alerts = alert_manager.get_alerts(status="acknowledged")
    assert len(alerts) == 1
    assert alerts[0]["acknowledged_by"] == "test_user"
    assert alerts[0]["acknowledged_at"] is not None

def test_resolve_alert(alert_manager):
    """Test resolving an alert."""
    alert_id = alert_manager.create_alert("test", "Test alert")
    
    # Resolve alert
    assert alert_manager.resolve_alert(alert_id)
    
    # Verify status
    alerts = alert_manager.get_alerts(status="resolved")
    assert len(alerts) == 1
    assert alerts[0]["resolved_at"] is not None

def test_get_active_alerts_count(alert_manager):
    """Test getting count of active alerts by severity."""
    # Create alerts with different severities
    alert_manager.create_alert("test", "Alert 1", "info")
    alert_manager.create_alert("test", "Alert 2", "warning")
    alert_manager.create_alert("test", "Alert 3", "error")
    
    counts = alert_manager.get_active_alerts_count()
    assert counts["info"] == 1
    assert counts["warning"] == 1
    assert counts["error"] == 1

def test_delete_old_alerts(alert_manager):
    """Test deleting old alerts."""
    # Create an old alert
    old_alert = {
        'alert_type': 'test',
        'message': 'Old alert',
        'severity': 'info',
        'status': 'active',
        'source': 'system',  # Add required source field
        'created_at_evie': datetime.now() - timedelta(days=2)
    }
    alert_manager.db.insert_data('alerts', [old_alert])
    
    # Delete alerts older than 1 day
    deleted_count = alert_manager.delete_old_alerts(days=1)
    assert deleted_count == 1
    
    # Verify old alert is gone
    alerts = alert_manager.get_alerts()
    assert len(alerts) == 0

def test_get_alert_statistics(alert_manager):
    """Test getting alert statistics."""
    # Create test alerts
    alert_manager.create_alert("type1", "Alert 1", "info")
    alert_manager.create_alert("type1", "Alert 2", "warning")
    alert_manager.create_alert("type2", "Alert 3", "error")
    
    stats = alert_manager.get_alert_statistics()
    assert "by_status" in stats
    assert "by_severity" in stats
    assert "by_type" in stats
    assert stats["by_type"]["type1"] == 2
    assert stats["by_type"]["type2"] == 1

def test_get_alert_trends(alert_manager):
    """Test getting alert trends."""
    # Create test alerts
    alert_manager.create_alert("test", "Alert 1", "info")
    alert_manager.create_alert("test", "Alert 2", "warning")
    
    trends = alert_manager.get_alert_trends(days=7)
    assert "daily" in trends
    assert "resolution_time" in trends

def test_get_source_statistics(alert_manager):
    """Test getting source statistics."""
    # Create test alerts
    alert_manager.create_alert("test", "Alert 1", "info")
    alert_manager.create_alert("test", "Alert 2", "warning")
    alert_manager.create_alert("test", "Alert 3", "error")
    
    stats = alert_manager.get_source_statistics()
    assert "system" in stats  # Default source
    assert stats["system"]["total"] == 3

def test_get_alert_metrics(alert_manager):
    """Test getting alert metrics."""
    # Create test alerts
    alert_manager.create_alert("test", "Alert 1", "info")
    alert_manager.create_alert("test", "Alert 2", "critical")
    
    metrics = alert_manager.get_alert_metrics(time_period="24h")
    assert "total_alerts" in metrics
    assert "resolution_rate" in metrics
    assert "critical_percentage" in metrics
    assert metrics["total_alerts"] == 2
    assert metrics["critical_percentage"] == 50.0

def test_query_alerts(alert_manager):
    """Test generic query function."""
    # Create test alerts
    alert_manager.create_alert("type1", "Alert 1", "info")
    alert_manager.create_alert("type2", "Alert 2", "warning")
    
    # Test selecting specific columns
    results = alert_manager.query_alerts(
        columns=["alert_type", "message"],
        filters={"severity": "info"},
        order_by="created_at_evie DESC"
    )
    assert len(results) == 1
    assert "alert_type" in results[0]
    assert "message" in results[0]
    assert "severity" not in results[0] 