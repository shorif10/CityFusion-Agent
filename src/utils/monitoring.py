"""Monitoring and metrics utilities for CityFusion-Agent."""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass 
class AgentMetrics:
    """Agent-specific metrics."""
    agent_name: str
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_response_time: float = 0.0
    last_query_time: Optional[datetime] = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_queries == 0:
            return 0.0
        return (self.successful_queries / self.total_queries) * 100
    
    def add_query_result(self, success: bool, response_time: float) -> None:
        """Add a query result to metrics."""
        self.total_queries += 1
        self.last_query_time = datetime.now()
        self.response_times.append(response_time)
        
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        # Update average response time
        self.average_response_time = sum(self.response_times) / len(self.response_times)


class SystemMonitor:
    """System resource monitoring."""
    
    def __init__(self, sampling_interval: int = 60):
        self.sampling_interval = sampling_interval
        self.metrics_history: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self) -> None:
        """Start system monitoring in a background thread."""
        if self.is_monitoring:
            logger.warning("System monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("System monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.sampling_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(self.sampling_interval)
    
    def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_mb = memory.used / (1024 * 1024)
        
        # Disk usage (for the root directory)
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        
        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            disk_usage_percent=disk_usage_percent,
            response_time_ms=0.0  # This will be updated by application metrics
        )
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent system metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return self._collect_system_metrics()
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary of metrics for the specified time period."""
        if not self.metrics_history:
            return {"error": "No metrics data available"}
        
        # Filter metrics for the specified time period
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": f"No metrics data available for the last {hours} hours"}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_usage_percent for m in recent_metrics]
        
        return {
            "time_period_hours": hours,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values)
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values)
            },
            "disk": {
                "avg": sum(disk_values) / len(disk_values),
                "min": min(disk_values),
                "max": max(disk_values)
            }
        }


class ApplicationMonitor:
    """Application-level monitoring and metrics."""
    
    def __init__(self):
        self.agent_metrics: Dict[str, AgentMetrics] = defaultdict(
            lambda: AgentMetrics(agent_name="unknown")
        )
        self.system_monitor = SystemMonitor()
        self.start_time = datetime.now()
        self.error_counts: defaultdict = defaultdict(int)
        self.api_call_counts: defaultdict = defaultdict(int)
    
    def start_monitoring(self) -> None:
        """Start all monitoring components."""
        self.system_monitor.start_monitoring()
        logger.info("Application monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop all monitoring components."""
        self.system_monitor.stop_monitoring()
        logger.info("Application monitoring stopped")
    
    def record_agent_query(self, agent_name: str, success: bool, response_time: float) -> None:
        """Record an agent query result."""
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
        
        self.agent_metrics[agent_name].add_query_result(success, response_time)
    
    def record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        self.error_counts[error_type] += 1
    
    def record_api_call(self, api_name: str) -> None:
        """Record an API call."""
        self.api_call_counts[api_name] += 1
    
    def get_application_summary(self) -> Dict[str, Any]:
        """Get comprehensive application metrics summary."""
        uptime = datetime.now() - self.start_time
        
        # Agent metrics summary
        agent_summary = {}
        for agent_name, metrics in self.agent_metrics.items():
            agent_summary[agent_name] = {
                "total_queries": metrics.total_queries,
                "success_rate": metrics.success_rate,
                "average_response_time": metrics.average_response_time,
                "last_query": metrics.last_query_time.isoformat() if metrics.last_query_time else None
            }
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": str(uptime),
            "agents": agent_summary,
            "errors": dict(self.error_counts),
            "api_calls": dict(self.api_call_counts),
            "system_metrics": self.system_monitor.get_current_metrics().__dict__ if self.system_monitor.get_current_metrics() else None
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status."""
        current_metrics = self.system_monitor.get_current_metrics()
        
        # Define health thresholds
        cpu_warning_threshold = 80.0
        memory_warning_threshold = 85.0
        disk_warning_threshold = 90.0
        
        health_status = "healthy"
        warnings = []
        
        if current_metrics:
            if current_metrics.cpu_percent > cpu_warning_threshold:
                health_status = "warning"
                warnings.append(f"High CPU usage: {current_metrics.cpu_percent:.1f}%")
            
            if current_metrics.memory_percent > memory_warning_threshold:
                health_status = "warning"
                warnings.append(f"High memory usage: {current_metrics.memory_percent:.1f}%")
            
            if current_metrics.disk_usage_percent > disk_warning_threshold:
                health_status = "warning"
                warnings.append(f"High disk usage: {current_metrics.disk_usage_percent:.1f}%")
        
        # Check for high error rates
        total_queries = sum(metrics.total_queries for metrics in self.agent_metrics.values())
        total_errors = sum(self.error_counts.values())
        
        if total_queries > 0:
            error_rate = (total_errors / total_queries) * 100
            if error_rate > 10:  # 10% error rate threshold
                health_status = "warning"
                warnings.append(f"High error rate: {error_rate:.1f}%")
        
        return {
            "status": health_status,
            "warnings": warnings,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_queries": total_queries,
            "total_errors": total_errors
        }


# Global application monitor instance
app_monitor = ApplicationMonitor()


# Export important classes and instances
__all__ = [
    "PerformanceMetrics", 
    "AgentMetrics", 
    "SystemMonitor", 
    "ApplicationMonitor", 
    "app_monitor"
]