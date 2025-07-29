"""
Memory optimization and management for BlastDock
"""

import gc
import os
import sys
import time
import threading
import weakref
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import tracemalloc

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: float
    rss_mb: float
    vms_mb: float
    percent: float
    python_objects: int
    gc_collections: Dict[str, int]
    top_allocations: List[Dict[str, Any]]


class MemoryOptimizer:
    """Memory optimization and monitoring system"""
    
    def __init__(self):
        """Initialize memory optimizer"""
        self.logger = get_logger(__name__)
        
        # Memory monitoring
        self._monitoring_enabled = False
        self._monitoring_thread = None
        self._monitoring_interval = 60  # 1 minute
        self._memory_snapshots: List[MemorySnapshot] = []
        self._max_snapshots = 100
        
        # Memory thresholds
        self.memory_warning_threshold = 80  # % of system memory
        self.memory_critical_threshold = 90  # % of system memory
        self.max_cache_memory_mb = 256  # Maximum cache memory
        
        # Optimization settings
        self.gc_optimization_enabled = True
        self.weak_reference_tracking = True
        self.automatic_cleanup_enabled = True
        
        # Object tracking
        self._tracked_objects = weakref.WeakSet()
        self._cleanup_callbacks: List[Callable] = []
        
        # Performance metrics
        self.metrics = {
            'cleanup_runs': 0,
            'objects_cleaned': 0,
            'memory_warnings': 0,
            'gc_collections_forced': 0,
            'peak_memory_mb': 0,
            'optimization_time_saved': 0
        }
        
        # Initialize memory tracking
        if hasattr(tracemalloc, 'start'):
            try:
                tracemalloc.start()
                self.logger.debug("Memory tracing enabled")
            except Exception as e:
                self.logger.warning(f"Could not enable memory tracing: {e}")
        
        self.logger.debug("Memory optimizer initialized")
    
    def start_monitoring(self, interval: float = 60):
        """Start memory monitoring"""
        if self._monitoring_enabled:
            return
        
        self._monitoring_interval = interval
        self._monitoring_enabled = True
        
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name='memory-monitor',
            daemon=True
        )
        self._monitoring_thread.start()
        
        self.logger.info(f"Memory monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        if not self._monitoring_enabled:
            return
        
        self._monitoring_enabled = False
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
        
        self.logger.info("Memory monitoring stopped")
    
    def _monitoring_loop(self):
        """Memory monitoring loop"""
        while self._monitoring_enabled:
            try:
                snapshot = self._take_memory_snapshot()
                self._process_memory_snapshot(snapshot)
                
                time.sleep(self._monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                time.sleep(self._monitoring_interval)
    
    def _take_memory_snapshot(self) -> MemorySnapshot:
        """Take a memory usage snapshot"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            rss_mb = memory_info.rss / 1024 / 1024
            vms_mb = memory_info.vms / 1024 / 1024
            
        except ImportError:
            # Fallback without psutil
            rss_mb = 0
            vms_mb = 0
            memory_percent = 0
        
        # Get Python object count
        python_objects = len(gc.get_objects())
        
        # Get GC collection counts
        gc_stats = gc.get_stats()
        gc_collections = {
            f"generation_{i}": stats['collections'] 
            for i, stats in enumerate(gc_stats)
        }
        
        # Get top memory allocations
        top_allocations = []
        if hasattr(tracemalloc, 'take_snapshot'):
            try:
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')[:10]
                
                for stat in top_stats:
                    top_allocations.append({
                        'size_mb': stat.size / 1024 / 1024,
                        'count': stat.count,
                        'filename': stat.traceback.format()[-1] if stat.traceback else 'unknown'
                    })
            except Exception:
                pass
        
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            rss_mb=rss_mb,
            vms_mb=vms_mb,
            percent=memory_percent,
            python_objects=python_objects,
            gc_collections=gc_collections,
            top_allocations=top_allocations
        )
        
        # Store snapshot
        self._memory_snapshots.append(snapshot)
        if len(self._memory_snapshots) > self._max_snapshots:
            self._memory_snapshots.pop(0)
        
        # Update peak memory
        if rss_mb > self.metrics['peak_memory_mb']:
            self.metrics['peak_memory_mb'] = rss_mb
        
        return snapshot
    
    def _process_memory_snapshot(self, snapshot: MemorySnapshot):
        """Process memory snapshot and trigger optimizations"""
        # Check memory thresholds
        if snapshot.percent > self.memory_critical_threshold:
            self.logger.warning(f"Critical memory usage: {snapshot.percent:.1f}%")
            self.metrics['memory_warnings'] += 1
            self.force_cleanup()
            
        elif snapshot.percent > self.memory_warning_threshold:
            self.logger.warning(f"High memory usage: {snapshot.percent:.1f}%")
            self.metrics['memory_warnings'] += 1
            self.optimize_memory()
        
        # Check for memory leaks (rapid growth)
        if len(self._memory_snapshots) >= 3:
            recent_snapshots = self._memory_snapshots[-3:]
            memory_growth = (recent_snapshots[-1].rss_mb - recent_snapshots[0].rss_mb)
            
            if memory_growth > 100:  # More than 100MB growth in 3 intervals
                self.logger.warning(f"Potential memory leak detected: {memory_growth:.1f}MB growth")
                self.optimize_memory()
    
    def optimize_memory(self):
        """Perform memory optimization"""
        start_time = time.time()
        initial_objects = len(gc.get_objects())
        
        self.logger.debug("Starting memory optimization")
        
        # 1. Run garbage collection
        if self.gc_optimization_enabled:
            collected = self._optimize_garbage_collection()
            self.logger.debug(f"Garbage collection freed {collected} objects")
        
        # 2. Run cleanup callbacks
        objects_cleaned = self._run_cleanup_callbacks()
        
        # 3. Optimize weak references
        if self.weak_reference_tracking:
            self._cleanup_weak_references()
        
        # 4. Clear internal caches
        self._clear_internal_caches()
        
        # Update metrics
        final_objects = len(gc.get_objects())
        objects_freed = initial_objects - final_objects
        optimization_time = time.time() - start_time
        
        self.metrics['cleanup_runs'] += 1
        self.metrics['objects_cleaned'] += objects_cleaned + objects_freed
        self.metrics['optimization_time_saved'] += optimization_time
        
        self.logger.debug(f"Memory optimization completed: {objects_freed} objects freed, {optimization_time:.3f}s")
    
    def force_cleanup(self):
        """Force aggressive memory cleanup"""
        self.logger.info("Forcing aggressive memory cleanup")
        
        # Run multiple GC cycles
        for generation in range(3):
            collected = gc.collect(generation)
            self.logger.debug(f"GC generation {generation}: {collected} objects collected")
        
        # Force optimization
        self.optimize_memory()
        
        # Clear all possible caches
        self._clear_all_caches()
        
        self.logger.info("Aggressive memory cleanup completed")
    
    def _optimize_garbage_collection(self) -> int:
        """Optimize garbage collection"""
        total_collected = 0
        
        # Adjust GC thresholds for better performance
        current_thresholds = gc.get_threshold()
        optimized_thresholds = (
            current_thresholds[0] * 2,  # Less frequent GC for generation 0
            current_thresholds[1],      # Keep generation 1 the same
            current_thresholds[2] // 2  # More frequent GC for generation 2
        )
        gc.set_threshold(*optimized_thresholds)
        
        # Run garbage collection for each generation
        for generation in range(3):
            collected = gc.collect(generation)
            total_collected += collected
        
        self.metrics['gc_collections_forced'] += 1
        return total_collected
    
    def _run_cleanup_callbacks(self) -> int:
        """Run registered cleanup callbacks"""
        objects_cleaned = 0
        
        for callback in self._cleanup_callbacks[:]:  # Copy to avoid modification during iteration
            try:
                result = callback()
                if isinstance(result, int):
                    objects_cleaned += result
            except Exception as e:
                self.logger.error(f"Cleanup callback failed: {e}")
                # Remove failed callback
                try:
                    self._cleanup_callbacks.remove(callback)
                except ValueError:
                    pass
        
        return objects_cleaned
    
    def _cleanup_weak_references(self):
        """Cleanup dead weak references"""
        # This is automatically handled by the WeakSet, but we can force cleanup
        try:
            # Access the WeakSet to trigger cleanup of dead references
            len(self._tracked_objects)
        except Exception:
            pass
    
    def _clear_internal_caches(self):
        """Clear internal Python caches"""
        # Clear method cache
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()
        
        # Clear regex cache
        try:
            import re
            re.purge()
        except Exception:
            pass
        
        # Clear linecache
        try:
            import linecache
            linecache.clearcache()
        except Exception:
            pass
    
    def _clear_all_caches(self):
        """Clear all possible caches"""
        self._clear_internal_caches()
        
        # Clear import cache for modules
        try:
            if hasattr(sys, 'modules'):
                # Don't clear core modules, just user modules
                user_modules = [
                    name for name in sys.modules.keys()
                    if name.startswith('blastdock') and not name.endswith('__main__')
                ]
                
                for module_name in user_modules:
                    module = sys.modules.get(module_name)
                    if hasattr(module, '__dict__'):
                        # Clear module-level caches
                        for attr_name in list(module.__dict__.keys()):
                            if attr_name.startswith('_cache') or attr_name.endswith('_cache'):
                                try:
                                    delattr(module, attr_name)
                                except Exception:
                                    pass
        except Exception:
            pass
    
    def register_cleanup_callback(self, callback: Callable) -> None:
        """Register a cleanup callback function"""
        if callable(callback):
            self._cleanup_callbacks.append(callback)
            self.logger.debug(f"Registered cleanup callback: {callback.__name__}")
    
    def unregister_cleanup_callback(self, callback: Callable) -> None:
        """Unregister a cleanup callback function"""
        try:
            self._cleanup_callbacks.remove(callback)
            self.logger.debug(f"Unregistered cleanup callback: {callback.__name__}")
        except ValueError:
            pass
    
    def track_object(self, obj: Any) -> None:
        """Track an object for memory monitoring"""
        if self.weak_reference_tracking:
            try:
                self._tracked_objects.add(obj)
            except TypeError:
                # Object is not weakly referenceable
                pass
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024,
                'python_objects': len(gc.get_objects()),
                'tracked_objects': len(self._tracked_objects),
                'gc_counts': gc.get_count()
            }
        except ImportError:
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0,
                'python_objects': len(gc.get_objects()),
                'tracked_objects': len(self._tracked_objects),
                'gc_counts': gc.get_count()
            }
    
    def get_memory_snapshots(self, limit: int = 10) -> List[MemorySnapshot]:
        """Get recent memory snapshots"""
        return self._memory_snapshots[-limit:]
    
    def get_memory_trend(self) -> Dict[str, Any]:
        """Get memory usage trend analysis"""
        if len(self._memory_snapshots) < 2:
            return {
                'trend': 'insufficient_data',
                'growth_rate_mb_per_hour': 0,
                'projected_peak_hours': 0
            }
        
        # Calculate growth rate
        first_snapshot = self._memory_snapshots[0]
        last_snapshot = self._memory_snapshots[-1]
        
        time_diff_hours = (last_snapshot.timestamp - first_snapshot.timestamp) / 3600
        memory_diff_mb = last_snapshot.rss_mb - first_snapshot.rss_mb
        
        if time_diff_hours > 0:
            growth_rate = memory_diff_mb / time_diff_hours
        else:
            growth_rate = 0
        
        # Determine trend
        if growth_rate > 10:  # More than 10MB/hour growth
            trend = 'increasing'
        elif growth_rate < -5:  # More than 5MB/hour decrease
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Project time to memory limit (if growing)
        projected_peak_hours = 0
        if growth_rate > 0:
            try:
                import psutil
                available_memory_mb = psutil.virtual_memory().available / 1024 / 1024
                projected_peak_hours = available_memory_mb / growth_rate
            except ImportError:
                projected_peak_hours = 0
        
        return {
            'trend': trend,
            'growth_rate_mb_per_hour': growth_rate,
            'projected_peak_hours': projected_peak_hours,
            'snapshots_analyzed': len(self._memory_snapshots)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get memory optimization performance metrics"""
        return {
            **self.metrics,
            'monitoring_enabled': self._monitoring_enabled,
            'monitoring_interval': self._monitoring_interval,
            'snapshots_collected': len(self._memory_snapshots),
            'cleanup_callbacks_registered': len(self._cleanup_callbacks),
            'memory_thresholds': {
                'warning': self.memory_warning_threshold,
                'critical': self.memory_critical_threshold
            }
        }
    
    def configure_thresholds(self, warning_threshold: float, critical_threshold: float):
        """Configure memory warning thresholds"""
        self.memory_warning_threshold = max(0, min(100, warning_threshold))
        self.memory_critical_threshold = max(0, min(100, critical_threshold))
        
        self.logger.info(f"Memory thresholds updated: warning={self.memory_warning_threshold}%, critical={self.memory_critical_threshold}%")
    
    def close(self):
        """Close memory optimizer and cleanup resources"""
        self.stop_monitoring()
        
        # Final cleanup
        if self.automatic_cleanup_enabled:
            self.optimize_memory()
        
        # Stop memory tracing
        if hasattr(tracemalloc, 'stop'):
            try:
                tracemalloc.stop()
            except Exception:
                pass
        
        self.logger.debug("Memory optimizer closed")


# Memory optimization decorator
def memory_optimized(cleanup_after: bool = True, track_memory: bool = True):
    """Decorator for memory-optimized function execution"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            memory_optimizer = get_memory_optimizer()
            
            # Track memory before execution
            if track_memory:
                initial_memory = memory_optimizer.get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Cleanup after execution
                if cleanup_after:
                    memory_optimizer.optimize_memory()
                
                # Log memory usage
                if track_memory:
                    final_memory = memory_optimizer.get_memory_usage()
                    memory_diff = final_memory['rss_mb'] - initial_memory['rss_mb']
                    
                    if abs(memory_diff) > 10:  # Log if significant change
                        logger.debug(
                            f"Function {func.__name__} memory change: {memory_diff:+.1f}MB "
                            f"({initial_memory['rss_mb']:.1f} -> {final_memory['rss_mb']:.1f}MB)"
                        )
        
        return wrapper
    return decorator


# Global memory optimizer instance
_memory_optimizer = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer instance"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer