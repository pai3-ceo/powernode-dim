"""
Unit tests for Monitoring system
"""

import pytest
from unittest.mock import Mock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'orchestrator' / 'src'))

from monitoring import Monitoring, MetricsCollector


def test_metrics_collector_initialization(test_config):
    """Test metrics collector initialization"""
    collector = MetricsCollector(test_config)
    
    assert collector.enabled is True
    assert len(collector.counters) == 0
    assert len(collector.gauges) == 0


def test_increment_counter(test_config):
    """Test incrementing counter"""
    collector = MetricsCollector(test_config)
    
    collector.increment('test.counter')
    collector.increment('test.counter', value=5)
    
    assert collector.counters['test.counter'] == 6


def test_set_gauge(test_config):
    """Test setting gauge"""
    collector = MetricsCollector(test_config)
    
    collector.set_gauge('test.gauge', 42.5)
    
    assert collector.gauges['test.gauge'] == 42.5


def test_record_timing(test_config):
    """Test recording timing"""
    collector = MetricsCollector(test_config)
    
    collector.record_timing('test.timing', 1.5)
    collector.record_timing('test.timing', 2.0)
    collector.record_timing('test.timing', 2.5)
    
    metrics = collector.get_metrics()
    assert 'test.timing' in metrics['timers']
    assert metrics['timers']['test.timing']['count'] == 3
    assert metrics['timers']['test.timing']['avg'] == 2.0


def test_record_histogram(test_config):
    """Test recording histogram"""
    collector = MetricsCollector(test_config)
    
    for i in range(10):
        collector.record_histogram('test.histogram', float(i))
    
    metrics = collector.get_metrics()
    assert 'test.histogram' in metrics['histograms']
    assert metrics['histograms']['test.histogram']['count'] == 10
    assert metrics['histograms']['test.histogram']['min'] == 0
    assert metrics['histograms']['test.histogram']['max'] == 9


def test_monitoring_integration(test_config):
    """Test monitoring integration"""
    monitoring = Monitoring(test_config)
    
    monitoring.record_job_submission('collaborative', 'user-001')
    monitoring.record_job_completion('collaborative', 45.5, True)
    monitoring.update_active_jobs(5)
    monitoring.update_node_count(10)
    
    metrics = monitoring.get_metrics()
    assert 'counters' in metrics
    assert 'gauges' in metrics

