"""
Monitoring - Advanced monitoring and metrics collection
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict, deque
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, config: Dict):
        """
        Initialize metrics collector
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.enabled = config.get('monitoring', {}).get('enabled', True)
        
        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        logger.info("Metrics Collector initialized")
    
    def increment(self, metric_name: str, value: int = 1, tags: Optional[Dict] = None):
        """Increment counter metric"""
        if not self.enabled:
            return
        
        key = self._build_key(metric_name, tags)
        self.counters[key] += value
    
    def set_gauge(self, metric_name: str, value: float, tags: Optional[Dict] = None):
        """Set gauge metric"""
        if not self.enabled:
            return
        
        key = self._build_key(metric_name, tags)
        self.gauges[key] = value
    
    def record_histogram(self, metric_name: str, value: float, tags: Optional[Dict] = None):
        """Record histogram value"""
        if not self.enabled:
            return
        
        key = self._build_key(metric_name, tags)
        self.histograms[key].append(value)
    
    def record_timing(self, metric_name: str, duration: float, tags: Optional[Dict] = None):
        """Record timing metric"""
        if not self.enabled:
            return
        
        key = self._build_key(metric_name, tags)
        self.timers[key].append(duration)
        
        # Keep only last 1000 timings
        if len(self.timers[key]) > 1000:
            self.timers[key] = self.timers[key][-1000:]
    
    def _build_key(self, metric_name: str, tags: Optional[Dict]) -> str:
        """Build metric key with tags"""
        if not tags:
            return metric_name
        
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric_name}[{tag_str}]"
    
    def get_metrics(self) -> Dict:
        """Get all metrics"""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {
                k: {
                    'count': len(v),
                    'min': min(v) if v else 0,
                    'max': max(v) if v else 0,
                    'avg': sum(v) / len(v) if v else 0,
                    'p50': self._percentile(v, 50) if v else 0,
                    'p95': self._percentile(v, 95) if v else 0,
                    'p99': self._percentile(v, 99) if v else 0
                }
                for k, v in self.histograms.items()
            },
            'timers': {
                k: {
                    'count': len(v),
                    'min': min(v) if v else 0,
                    'max': max(v) if v else 0,
                    'avg': sum(v) / len(v) if v else 0,
                    'p50': self._percentile(v, 50) if v else 0,
                    'p95': self._percentile(v, 95) if v else 0,
                    'p99': self._percentile(v, 99) if v else 0
                }
                for k, v in self.timers.items()
            }
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """Reset all metrics"""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()


class Monitoring:
    """Advanced monitoring system"""
    
    def __init__(self, config: Dict):
        """
        Initialize monitoring
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.metrics = MetricsCollector(config)
        
        logger.info("Monitoring initialized")
    
    def record_job_submission(self, pattern: str, user_id: str):
        """Record job submission"""
        self.metrics.increment('dim.jobs.submitted', tags={'pattern': pattern, 'user_id': user_id})
    
    def record_job_completion(self, pattern: str, duration: float, success: bool):
        """Record job completion"""
        status = 'success' if success else 'failure'
        self.metrics.increment('dim.jobs.completed', tags={'pattern': pattern, 'status': status})
        self.metrics.record_timing('dim.jobs.duration', duration, tags={'pattern': pattern, 'status': status})
    
    def record_node_selection(self, node_count: int):
        """Record node selection"""
        self.metrics.record_histogram('dim.nodes.selected', node_count)
    
    def record_api_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record API request"""
        self.metrics.increment('dim.api.requests', tags={'endpoint': endpoint, 'method': method, 'status': status_code})
        self.metrics.record_timing('dim.api.duration', duration, tags={'endpoint': endpoint, 'method': method})
    
    def update_active_jobs(self, count: int):
        """Update active jobs gauge"""
        self.metrics.set_gauge('dim.jobs.active', count)
    
    def update_node_count(self, count: int):
        """Update node count gauge"""
        self.metrics.set_gauge('dim.nodes.total', count)
    
    def get_metrics(self) -> Dict:
        """Get all metrics"""
        return self.metrics.get_metrics()

