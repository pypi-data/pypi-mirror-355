"""
WolfPy Performance Optimization Module.

This module provides comprehensive performance monitoring, optimization,
and profiling capabilities for WolfPy applications.
"""

import time
import threading
import psutil
import gc
import sys
import traceback
import cProfile
import pstats
import io
from typing import Dict, List, Any, Optional, Callable, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import weakref


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RequestMetrics:
    """Request-level performance metrics."""
    request_id: str
    method: str
    path: str
    start_time: float
    end_time: Optional[float] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    database_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: List[str] = field(default_factory=list)


class PerformanceProfiler:
    """Advanced performance profiler with detailed metrics."""
    
    def __init__(self, enabled: bool = True, sample_rate: float = 1.0):
        """
        Initialize performance profiler.
        
        Args:
            enabled: Whether profiling is enabled
            sample_rate: Sampling rate (0.0 to 1.0)
        """
        self.enabled = enabled
        self.sample_rate = sample_rate
        self._profiles = {}
        self._active_profiles = {}
        self._lock = threading.RLock()
    
    def profile(self, name: str):
        """Decorator for profiling functions."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled or not self._should_sample():
                    return func(*args, **kwargs)
                
                with self.profile_context(f"{name}:{func.__name__}"):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def profile_context(self, name: str):
        """Context manager for profiling code blocks."""
        return ProfileContext(self, name)
    
    def start_profile(self, name: str) -> str:
        """Start profiling a named operation."""
        if not self.enabled:
            return ""
        
        profile_id = f"{name}_{time.time()}_{threading.get_ident()}"
        
        with self._lock:
            self._active_profiles[profile_id] = {
                'name': name,
                'start_time': time.time(),
                'start_cpu': time.process_time(),
                'start_memory': self._get_memory_usage(),
                'thread_id': threading.get_ident()
            }
        
        return profile_id
    
    def end_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """End profiling and return metrics."""
        if not self.enabled or not profile_id:
            return None
        
        end_time = time.time()
        end_cpu = time.process_time()
        end_memory = self._get_memory_usage()
        
        with self._lock:
            if profile_id not in self._active_profiles:
                return None
            
            profile_data = self._active_profiles.pop(profile_id)
            
            metrics = {
                'name': profile_data['name'],
                'duration': end_time - profile_data['start_time'],
                'cpu_time': end_cpu - profile_data['start_cpu'],
                'memory_delta': end_memory - profile_data['start_memory'],
                'start_time': profile_data['start_time'],
                'end_time': end_time,
                'thread_id': profile_data['thread_id']
            }
            
            # Store in profiles history
            if profile_data['name'] not in self._profiles:
                self._profiles[profile_data['name']] = deque(maxlen=1000)
            
            self._profiles[profile_data['name']].append(metrics)
            
            return metrics
    
    def _should_sample(self) -> bool:
        """Determine if this request should be sampled."""
        import random
        return random.random() < self.sample_rate
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def get_profile_stats(self, name: str = None) -> Dict[str, Any]:
        """Get profiling statistics."""
        with self._lock:
            if name:
                if name not in self._profiles:
                    return {}
                
                profiles = list(self._profiles[name])
                if not profiles:
                    return {}
                
                durations = [p['duration'] for p in profiles]
                cpu_times = [p['cpu_time'] for p in profiles]
                memory_deltas = [p['memory_delta'] for p in profiles]
                
                return {
                    'name': name,
                    'count': len(profiles),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'avg_cpu_time': sum(cpu_times) / len(cpu_times),
                    'avg_memory_delta': sum(memory_deltas) / len(memory_deltas),
                    'recent_profiles': profiles[-10:]
                }
            else:
                # Return stats for all profiles
                stats = {}
                for profile_name in self._profiles:
                    stats[profile_name] = self.get_profile_stats(profile_name)
                return stats


class ProfileContext:
    """Context manager for profiling."""
    
    def __init__(self, profiler: PerformanceProfiler, name: str):
        self.profiler = profiler
        self.name = name
        self.profile_id = None
    
    def __enter__(self):
        self.profile_id = self.profiler.start_profile(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profile_id:
            self.profiler.end_profile(self.profile_id)


class MemoryMonitor:
    """Memory usage monitoring and leak detection."""
    
    def __init__(self, check_interval: float = 60.0):
        """
        Initialize memory monitor.
        
        Args:
            check_interval: Interval between memory checks in seconds
        """
        self.check_interval = check_interval
        self._memory_history = deque(maxlen=1000)
        self._object_counts = defaultdict(int)
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start memory monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                self._collect_memory_stats()
                time.sleep(self.check_interval)
            except Exception:
                pass
    
    def _collect_memory_stats(self):
        """Collect current memory statistics."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            stats = {
                'timestamp': time.time(),
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent(),
                'available': psutil.virtual_memory().available / 1024 / 1024,  # MB
                'gc_counts': gc.get_count(),
                'object_count': len(gc.get_objects())
            }
            
            with self._lock:
                self._memory_history.append(stats)
        
        except Exception:
            pass
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics."""
        with self._lock:
            if not self._memory_history:
                return {}
            
            recent_stats = list(self._memory_history)[-10:]
            current = recent_stats[-1] if recent_stats else {}
            
            if len(recent_stats) > 1:
                memory_trend = recent_stats[-1]['rss'] - recent_stats[0]['rss']
            else:
                memory_trend = 0.0
            
            return {
                'current_rss': current.get('rss', 0),
                'current_vms': current.get('vms', 0),
                'memory_percent': current.get('percent', 0),
                'available_memory': current.get('available', 0),
                'memory_trend': memory_trend,
                'gc_counts': current.get('gc_counts', (0, 0, 0)),
                'object_count': current.get('object_count', 0),
                'history_length': len(self._memory_history)
            }
    
    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks."""
        leaks = []
        
        with self._lock:
            if len(self._memory_history) < 10:
                return leaks
            
            # Check for consistent memory growth
            recent_stats = list(self._memory_history)[-10:]
            memory_values = [stat['rss'] for stat in recent_stats]
            
            # Simple trend detection
            if len(memory_values) >= 5:
                first_half = sum(memory_values[:len(memory_values)//2])
                second_half = sum(memory_values[len(memory_values)//2:])
                
                if second_half > first_half * 1.2:  # 20% increase
                    leaks.append({
                        'type': 'memory_growth',
                        'description': 'Consistent memory growth detected',
                        'growth_rate': (second_half - first_half) / first_half,
                        'current_memory': memory_values[-1]
                    })
        
        return leaks


class PerformanceOptimizer:
    """Automatic performance optimization."""
    
    def __init__(self):
        """Initialize performance optimizer."""
        self._optimizations = {}
        self._optimization_history = []
        self._enabled = True
    
    def register_optimization(self, name: str, optimizer: Callable):
        """Register an optimization function."""
        self._optimizations[name] = optimizer
    
    def run_optimizations(self, metrics: Dict[str, Any]) -> List[str]:
        """Run all registered optimizations."""
        if not self._enabled:
            return []
        
        applied_optimizations = []
        
        for name, optimizer in self._optimizations.items():
            try:
                if optimizer(metrics):
                    applied_optimizations.append(name)
                    self._optimization_history.append({
                        'name': name,
                        'timestamp': time.time(),
                        'metrics': metrics.copy()
                    })
            except Exception as e:
                # Log optimization error but continue
                pass
        
        return applied_optimizations
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """Get history of applied optimizations."""
        return self._optimization_history.copy()


class PerformanceManager:
    """Central performance management system."""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize performance manager.
        
        Args:
            enabled: Whether performance monitoring is enabled
        """
        self.enabled = enabled
        self.profiler = PerformanceProfiler(enabled)
        self.memory_monitor = MemoryMonitor()
        self.optimizer = PerformanceOptimizer()
        
        # Request tracking
        self._active_requests = {}
        self._request_history = deque(maxlen=10000)
        self._request_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'error_count': 0
        })
        
        # Performance alerts
        self._alert_thresholds = {
            'response_time': 1.0,  # seconds
            'memory_usage': 500.0,  # MB
            'error_rate': 0.05  # 5%
        }
        self._alerts = deque(maxlen=1000)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Start monitoring
        if enabled:
            self.memory_monitor.start_monitoring()
    
    def start_request(self, request_id: str, method: str, path: str) -> RequestMetrics:
        """Start tracking a request."""
        if not self.enabled:
            return None
        
        metrics = RequestMetrics(
            request_id=request_id,
            method=method,
            path=path,
            start_time=time.time()
        )
        
        with self._lock:
            self._active_requests[request_id] = metrics
        
        return metrics
    
    def end_request(self, request_id: str, status_code: int = 200) -> Optional[RequestMetrics]:
        """End tracking a request."""
        if not self.enabled:
            return None
        
        end_time = time.time()
        
        with self._lock:
            if request_id not in self._active_requests:
                return None
            
            metrics = self._active_requests.pop(request_id)
            metrics.end_time = end_time
            metrics.response_time = end_time - metrics.start_time
            metrics.status_code = status_code
            # Get current memory usage
            memory_stats = self.memory_monitor.get_memory_stats()
            metrics.memory_usage = memory_stats.get('current_rss', 0)
            
            # Store in history
            self._request_history.append(metrics)
            
            # Update stats
            path_stats = self._request_stats[metrics.path]
            path_stats['count'] += 1
            path_stats['total_time'] += metrics.response_time
            path_stats['avg_time'] = path_stats['total_time'] / path_stats['count']
            path_stats['min_time'] = min(path_stats['min_time'], metrics.response_time)
            path_stats['max_time'] = max(path_stats['max_time'], metrics.response_time)
            
            if status_code >= 400:
                path_stats['error_count'] += 1
            
            # Check for performance alerts
            self._check_alerts(metrics)
            
            return metrics
    
    def _check_alerts(self, metrics: RequestMetrics):
        """Check if any performance alerts should be triggered."""
        alerts = []
        
        # Response time alert
        if metrics.response_time > self._alert_thresholds['response_time']:
            alerts.append({
                'type': 'slow_response',
                'message': f"Slow response: {metrics.response_time:.3f}s for {metrics.path}",
                'timestamp': time.time(),
                'metrics': metrics
            })
        
        # Memory usage alert
        if metrics.memory_usage and metrics.memory_usage > self._alert_thresholds['memory_usage']:
            alerts.append({
                'type': 'high_memory',
                'message': f"High memory usage: {metrics.memory_usage:.1f}MB",
                'timestamp': time.time(),
                'metrics': metrics
            })
        
        # Add alerts to queue
        for alert in alerts:
            self._alerts.append(alert)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self._lock:
            # Request statistics
            total_requests = len(self._request_history)
            if total_requests > 0:
                recent_requests = list(self._request_history)[-100:]
                avg_response_time = sum(r.response_time for r in recent_requests) / len(recent_requests)
                error_count = sum(1 for r in recent_requests if r.status_code >= 400)
                error_rate = error_count / len(recent_requests)
            else:
                avg_response_time = 0.0
                error_count = 0
                error_rate = 0.0
            
            # Memory statistics
            memory_stats = self.memory_monitor.get_memory_stats()
            
            # Profiler statistics
            profile_stats = self.profiler.get_profile_stats()
            
            # Recent alerts
            recent_alerts = list(self._alerts)[-10:]
            
            return {
                'request_stats': {
                    'total_requests': total_requests,
                    'avg_response_time': avg_response_time,
                    'error_count': error_count,
                    'error_rate': error_rate,
                    'active_requests': len(self._active_requests)
                },
                'memory_stats': memory_stats,
                'profile_stats': profile_stats,
                'recent_alerts': recent_alerts,
                'path_stats': dict(self._request_stats)
            }
    
    def cleanup(self):
        """Cleanup resources."""
        if self.memory_monitor:
            self.memory_monitor.stop_monitoring()


# Global instances for easy access
performance_monitor = PerformanceManager()
memory_cache = {}  # Simple dict cache for now
resource_monitor = None  # Will be initialized when needed
