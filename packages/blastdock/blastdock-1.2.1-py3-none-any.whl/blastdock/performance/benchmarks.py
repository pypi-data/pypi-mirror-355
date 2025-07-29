"""
Performance benchmarking and monitoring system for BlastDock
"""

import time
import gc
import threading
from typing import Dict, List, Any, Optional, Callable, ContextManager
from dataclasses import dataclass, field
from contextlib import contextmanager
import statistics
from collections import defaultdict

from ..utils.logging import get_logger
from .cache import get_cache_manager
from .memory_optimizer import get_memory_optimizer

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a performance benchmark"""
    name: str
    duration: float
    memory_usage_mb: float
    memory_delta_mb: float
    cpu_percent: Optional[float] = None
    iterations: int = 1
    error_rate: float = 0.0
    throughput: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceProfile:
    """Performance profile for an operation"""
    operation: str
    avg_duration: float
    min_duration: float
    max_duration: float
    std_deviation: float
    avg_memory_mb: float
    sample_count: int
    percentiles: Dict[str, float]
    last_updated: float


class PerformanceBenchmarks:
    """Comprehensive performance benchmarking system"""
    
    def __init__(self):
        """Initialize performance benchmarks"""
        self.logger = get_logger(__name__)
        self.cache_manager = get_cache_manager()
        self.memory_optimizer = get_memory_optimizer()
        
        # Benchmark storage
        self._benchmark_results: Dict[str, List[BenchmarkResult]] = defaultdict(list)
        self._performance_profiles: Dict[str, PerformanceProfile] = {}
        self._benchmark_lock = threading.RLock()
        
        # Active benchmarks
        self._active_benchmarks: Dict[str, Dict[str, Any]] = {}
        
        # Performance thresholds
        self.performance_thresholds = {
            'template_load_ms': 5000,      # 5 seconds
            'deployment_start_ms': 30000,  # 30 seconds
            'cache_hit_rate': 80,          # 80%
            'memory_usage_mb': 500,        # 500MB
            'error_rate': 0.05             # 5%
        }
        
        # Monitoring configuration
        self.max_results_per_benchmark = 1000
        self.profile_update_threshold = 10  # Update profile after 10 samples
        
        self.logger.debug("Performance benchmarks initialized")
    
    @contextmanager
    def benchmark(self, name: str, iterations: int = 1, 
                 track_memory: bool = True, track_cpu: bool = False) -> ContextManager['BenchmarkContext']:
        """Context manager for benchmarking operations"""
        context = BenchmarkContext(
            name=name,
            iterations=iterations,
            track_memory=track_memory,
            track_cpu=track_cpu,
            benchmarks=self
        )
        
        with self._benchmark_lock:
            self._active_benchmarks[name] = {
                'start_time': time.time(),
                'context': context
            }
        
        try:
            yield context
        finally:
            with self._benchmark_lock:
                self._active_benchmarks.pop(name, None)
    
    def record_benchmark(self, result: BenchmarkResult):
        """Record a benchmark result"""
        with self._benchmark_lock:
            # Store result
            self._benchmark_results[result.name].append(result)
            
            # Limit stored results
            if len(self._benchmark_results[result.name]) > self.max_results_per_benchmark:
                self._benchmark_results[result.name].pop(0)
            
            # Update performance profile
            self._update_performance_profile(result.name)
        
        self.logger.debug(f"Recorded benchmark: {result.name} ({result.duration:.3f}s)")
    
    def _update_performance_profile(self, operation: str):
        """Update performance profile for an operation"""
        results = self._benchmark_results[operation]
        
        if len(results) < self.profile_update_threshold:
            return
        
        # Take recent results for profile
        recent_results = results[-100:]  # Last 100 results
        
        durations = [r.duration for r in recent_results]
        memory_usage = [r.memory_usage_mb for r in recent_results]
        
        # Calculate statistics
        avg_duration = statistics.mean(durations)
        min_duration = min(durations)
        max_duration = max(durations)
        std_deviation = statistics.stdev(durations) if len(durations) > 1 else 0
        avg_memory = statistics.mean(memory_usage)
        
        # Calculate percentiles
        sorted_durations = sorted(durations)
        percentiles = {
            'p50': self._percentile(sorted_durations, 50),
            'p75': self._percentile(sorted_durations, 75),
            'p90': self._percentile(sorted_durations, 90),
            'p95': self._percentile(sorted_durations, 95),
            'p99': self._percentile(sorted_durations, 99)
        }
        
        profile = PerformanceProfile(
            operation=operation,
            avg_duration=avg_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            std_deviation=std_deviation,
            avg_memory_mb=avg_memory,
            sample_count=len(recent_results),
            percentiles=percentiles,
            last_updated=time.time()
        )
        
        self._performance_profiles[operation] = profile
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not data:
            return 0
        
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f == len(data) - 1:
            return data[f]
        else:
            return data[f] * (1 - c) + data[f + 1] * c
    
    def get_benchmark_results(self, name: str, limit: int = 100) -> List[BenchmarkResult]:
        """Get recent benchmark results for an operation"""
        with self._benchmark_lock:
            results = self._benchmark_results.get(name, [])
            return results[-limit:]
    
    def get_performance_profile(self, operation: str) -> Optional[PerformanceProfile]:
        """Get performance profile for an operation"""
        return self._performance_profiles.get(operation)
    
    def get_all_profiles(self) -> Dict[str, PerformanceProfile]:
        """Get all performance profiles"""
        return self._performance_profiles.copy()
    
    def run_system_benchmark(self) -> Dict[str, BenchmarkResult]:
        """Run comprehensive system benchmark"""
        self.logger.info("Running system benchmark suite...")
        
        benchmark_results = {}
        
        # 1. Cache performance benchmark
        benchmark_results['cache_performance'] = self._benchmark_cache_performance()
        
        # 2. Memory allocation benchmark
        benchmark_results['memory_allocation'] = self._benchmark_memory_allocation()
        
        # 3. I/O performance benchmark
        benchmark_results['io_performance'] = self._benchmark_io_performance()
        
        # 4. CPU performance benchmark
        benchmark_results['cpu_performance'] = self._benchmark_cpu_performance()
        
        # 5. Template loading benchmark
        benchmark_results['template_loading'] = self._benchmark_template_loading()
        
        self.logger.info("System benchmark suite completed")
        return benchmark_results
    
    def _benchmark_cache_performance(self) -> BenchmarkResult:
        """Benchmark cache read/write performance"""
        iterations = 1000
        start_time = time.time()
        initial_memory = self.memory_optimizer.get_memory_usage()
        
        hit_count = 0
        
        # Test cache operations
        for i in range(iterations):
            key = f"benchmark_key_{i % 100}"  # Some overlap for hits
            
            # Try to get value
            value = self.cache_manager.get(key)
            if value is not None:
                hit_count += 1
            else:
                # Set new value
                self.cache_manager.set(key, f"benchmark_value_{i}", ttl=300)
        
        duration = time.time() - start_time
        final_memory = self.memory_optimizer.get_memory_usage()
        memory_delta = final_memory['rss_mb'] - initial_memory['rss_mb']
        
        hit_rate = hit_count / iterations
        throughput = iterations / duration
        
        return BenchmarkResult(
            name='cache_performance',
            duration=duration,
            memory_usage_mb=final_memory['rss_mb'],
            memory_delta_mb=memory_delta,
            iterations=iterations,
            throughput=throughput,
            metadata={
                'hit_rate': hit_rate,
                'operations_per_second': throughput
            }
        )
    
    def _benchmark_memory_allocation(self) -> BenchmarkResult:
        """Benchmark memory allocation and garbage collection"""
        iterations = 10000
        start_time = time.time()
        initial_memory = self.memory_optimizer.get_memory_usage()
        
        # Allocate and deallocate objects
        objects = []
        for i in range(iterations):
            # Allocate objects
            obj = {
                'id': i,
                'data': list(range(100)),
                'metadata': {'created': time.time(), 'index': i}
            }
            objects.append(obj)
            
            # Periodically clear some objects
            if i % 1000 == 0 and objects:
                objects = objects[500:]  # Keep recent half
                gc.collect()  # Force garbage collection
        
        # Final cleanup
        objects.clear()
        gc.collect()
        
        duration = time.time() - start_time
        final_memory = self.memory_optimizer.get_memory_usage()
        memory_delta = final_memory['rss_mb'] - initial_memory['rss_mb']
        
        throughput = iterations / duration
        
        return BenchmarkResult(
            name='memory_allocation',
            duration=duration,
            memory_usage_mb=final_memory['rss_mb'],
            memory_delta_mb=memory_delta,
            iterations=iterations,
            throughput=throughput,
            metadata={
                'allocations_per_second': throughput,
                'final_objects': len(gc.get_objects())
            }
        )
    
    def _benchmark_io_performance(self) -> BenchmarkResult:
        """Benchmark I/O performance"""
        import tempfile
        import os
        
        iterations = 100
        file_size_kb = 100  # 100KB files
        start_time = time.time()
        initial_memory = self.memory_optimizer.get_memory_usage()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test file I/O
            test_data = b'x' * (file_size_kb * 1024)
            
            for i in range(iterations):
                file_path = os.path.join(temp_dir, f'test_file_{i}.txt')
                
                # Write file
                with open(file_path, 'wb') as f:
                    f.write(test_data)
                
                # Read file
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                # Verify data
                assert len(data) == len(test_data)
                
                # Clean up
                os.unlink(file_path)
        
        duration = time.time() - start_time
        final_memory = self.memory_optimizer.get_memory_usage()
        memory_delta = final_memory['rss_mb'] - initial_memory['rss_mb']
        
        throughput = iterations / duration
        mb_per_second = (iterations * file_size_kb / 1024) / duration
        
        return BenchmarkResult(
            name='io_performance',
            duration=duration,
            memory_usage_mb=final_memory['rss_mb'],
            memory_delta_mb=memory_delta,
            iterations=iterations,
            throughput=throughput,
            metadata={
                'files_per_second': throughput,
                'mb_per_second': mb_per_second,
                'file_size_kb': file_size_kb
            }
        )
    
    def _benchmark_cpu_performance(self) -> BenchmarkResult:
        """Benchmark CPU performance"""
        iterations = 100000
        start_time = time.time()
        initial_memory = self.memory_optimizer.get_memory_usage()
        
        # CPU-intensive calculation
        result = 0
        for i in range(iterations):
            # Some mathematical operations
            result += i ** 2
            result = result % 1000000
        
        duration = time.time() - start_time
        final_memory = self.memory_optimizer.get_memory_usage()
        memory_delta = final_memory['rss_mb'] - initial_memory['rss_mb']
        
        throughput = iterations / duration
        
        return BenchmarkResult(
            name='cpu_performance',
            duration=duration,
            memory_usage_mb=final_memory['rss_mb'],
            memory_delta_mb=memory_delta,
            iterations=iterations,
            throughput=throughput,
            metadata={
                'operations_per_second': throughput,
                'final_result': result
            }
        )
    
    def _benchmark_template_loading(self) -> BenchmarkResult:
        """Benchmark template loading performance"""
        import tempfile
        import os
        import yaml
        
        iterations = 50
        start_time = time.time()
        initial_memory = self.memory_optimizer.get_memory_usage()
        
        # Create test templates
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_created = 0
            
            for i in range(iterations):
                template_dir = os.path.join(temp_dir, f'template_{i}')
                os.makedirs(template_dir)
                
                # Create docker-compose.yml
                compose_content = {
                    'version': '3.8',
                    'services': {
                        f'service_{j}': {
                            'image': f'nginx:{j}',
                            'ports': [f'{8000 + j}:80']
                        }
                        for j in range(3)  # 3 services per template
                    }
                }
                
                compose_file = os.path.join(template_dir, 'docker-compose.yml')
                with open(compose_file, 'w') as f:
                    yaml.dump(compose_content, f)
                
                # Create metadata file
                metadata = {
                    'name': f'test-template-{i}',
                    'description': f'Test template {i}',
                    'version': '1.0.0'
                }
                
                metadata_file = os.path.join(template_dir, 'blastdock.yml')
                with open(metadata_file, 'w') as f:
                    yaml.dump(metadata, f)
                
                templates_created += 1
            
            # Now benchmark loading the templates
            load_start = time.time()
            
            for i in range(iterations):
                template_dir = os.path.join(temp_dir, f'template_{i}')
                
                # Simulate template loading
                compose_file = os.path.join(template_dir, 'docker-compose.yml')
                with open(compose_file, 'r') as f:
                    compose_data = yaml.safe_load(f)
                
                metadata_file = os.path.join(template_dir, 'blastdock.yml')
                with open(metadata_file, 'r') as f:
                    metadata = yaml.safe_load(f)
                
                # Basic validation
                assert 'services' in compose_data
                assert len(compose_data['services']) == 3
                assert 'name' in metadata
            
            load_duration = time.time() - load_start
        
        duration = time.time() - start_time
        final_memory = self.memory_optimizer.get_memory_usage()
        memory_delta = final_memory['rss_mb'] - initial_memory['rss_mb']
        
        throughput = iterations / load_duration
        
        return BenchmarkResult(
            name='template_loading',
            duration=duration,
            memory_usage_mb=final_memory['rss_mb'],
            memory_delta_mb=memory_delta,
            iterations=iterations,
            throughput=throughput,
            metadata={
                'templates_per_second': throughput,
                'load_duration': load_duration,
                'templates_created': templates_created
            }
        )
    
    def analyze_performance_trends(self, operation: str, window_size: int = 50) -> Dict[str, Any]:
        """Analyze performance trends for an operation"""
        results = self.get_benchmark_results(operation, limit=window_size * 2)
        
        if len(results) < window_size:
            return {
                'trend': 'insufficient_data',
                'sample_size': len(results)
            }
        
        # Split into two windows for comparison
        older_results = results[:window_size]
        newer_results = results[-window_size:]
        
        # Calculate averages
        older_avg = statistics.mean(r.duration for r in older_results)
        newer_avg = statistics.mean(r.duration for r in newer_results)
        
        # Determine trend
        change_percent = ((newer_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        
        if abs(change_percent) < 5:
            trend = 'stable'
        elif change_percent > 0:
            trend = 'degrading'
        else:
            trend = 'improving'
        
        # Memory trend
        older_memory_avg = statistics.mean(r.memory_usage_mb for r in older_results)
        newer_memory_avg = statistics.mean(r.memory_usage_mb for r in newer_results)
        memory_change_percent = ((newer_memory_avg - older_memory_avg) / older_memory_avg * 100) if older_memory_avg > 0 else 0
        
        return {
            'trend': trend,
            'performance_change_percent': change_percent,
            'memory_change_percent': memory_change_percent,
            'older_avg_duration': older_avg,
            'newer_avg_duration': newer_avg,
            'older_memory_avg': older_memory_avg,
            'newer_memory_avg': newer_memory_avg,
            'sample_size': len(results),
            'window_size': window_size
        }
    
    def check_performance_thresholds(self) -> Dict[str, Any]:
        """Check if performance metrics exceed thresholds"""
        violations = []
        warnings = []
        
        # Check operation profiles against thresholds
        for operation, profile in self._performance_profiles.items():
            # Duration thresholds
            duration_ms = profile.avg_duration * 1000
            
            if 'template_load' in operation and duration_ms > self.performance_thresholds['template_load_ms']:
                violations.append({
                    'type': 'duration',
                    'operation': operation,
                    'value': duration_ms,
                    'threshold': self.performance_thresholds['template_load_ms'],
                    'severity': 'high'
                })
            
            elif 'deployment' in operation and duration_ms > self.performance_thresholds['deployment_start_ms']:
                violations.append({
                    'type': 'duration',
                    'operation': operation,
                    'value': duration_ms,
                    'threshold': self.performance_thresholds['deployment_start_ms'],
                    'severity': 'medium'
                })
            
            # Memory thresholds
            if profile.avg_memory_mb > self.performance_thresholds['memory_usage_mb']:
                warnings.append({
                    'type': 'memory',
                    'operation': operation,
                    'value': profile.avg_memory_mb,
                    'threshold': self.performance_thresholds['memory_usage_mb'],
                    'severity': 'medium'
                })
        
        # Check cache hit rate
        cache_stats = self.cache_manager.get_stats()
        if cache_stats.get('hit_rate', 0) < self.performance_thresholds['cache_hit_rate']:
            warnings.append({
                'type': 'cache_hit_rate',
                'operation': 'cache',
                'value': cache_stats.get('hit_rate', 0),
                'threshold': self.performance_thresholds['cache_hit_rate'],
                'severity': 'low'
            })
        
        return {
            'violations': violations,
            'warnings': warnings,
            'total_issues': len(violations) + len(warnings),
            'check_time': time.time()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        cache_stats = self.cache_manager.get_stats()
        memory_usage = self.memory_optimizer.get_memory_usage()
        
        # Calculate overall statistics
        total_benchmarks = sum(len(results) for results in self._benchmark_results.values())
        operations_profiled = len(self._performance_profiles)
        
        # Recent performance
        recent_results = []
        for operation_results in self._benchmark_results.values():
            recent_results.extend(operation_results[-10:])  # Last 10 per operation
        
        if recent_results:
            avg_duration = statistics.mean(r.duration for r in recent_results)
            avg_memory = statistics.mean(r.memory_usage_mb for r in recent_results)
        else:
            avg_duration = 0
            avg_memory = 0
        
        return {
            'total_benchmarks': total_benchmarks,
            'operations_profiled': operations_profiled,
            'recent_avg_duration': avg_duration,
            'recent_avg_memory_mb': avg_memory,
            'cache_hit_rate': cache_stats.get('hit_rate', 0),
            'memory_usage_mb': memory_usage['rss_mb'],
            'active_benchmarks': len(self._active_benchmarks),
            'performance_profiles': {
                name: {
                    'avg_duration': profile.avg_duration,
                    'sample_count': profile.sample_count
                }
                for name, profile in self._performance_profiles.items()
            }
        }
    
    def export_benchmark_data(self, file_path: str, operations: Optional[List[str]] = None):
        """Export benchmark data to file"""
        import json
        
        data_to_export = {}
        
        # Select operations to export
        operations_to_export = operations or list(self._benchmark_results.keys())
        
        for operation in operations_to_export:
            if operation in self._benchmark_results:
                results = self._benchmark_results[operation]
                data_to_export[operation] = [
                    {
                        'name': r.name,
                        'duration': r.duration,
                        'memory_usage_mb': r.memory_usage_mb,
                        'memory_delta_mb': r.memory_delta_mb,
                        'iterations': r.iterations,
                        'throughput': r.throughput,
                        'metadata': r.metadata
                    }
                    for r in results
                ]
        
        # Include performance profiles
        data_to_export['profiles'] = {
            operation: {
                'avg_duration': profile.avg_duration,
                'min_duration': profile.min_duration,
                'max_duration': profile.max_duration,
                'std_deviation': profile.std_deviation,
                'avg_memory_mb': profile.avg_memory_mb,
                'sample_count': profile.sample_count,
                'percentiles': profile.percentiles,
                'last_updated': profile.last_updated
            }
            for operation, profile in self._performance_profiles.items()
            if not operations or operation in operations
        }
        
        # Export to file
        with open(file_path, 'w') as f:
            json.dump(data_to_export, f, indent=2)
        
        self.logger.info(f"Exported benchmark data to {file_path}")
    
    def clear_benchmark_data(self, operation: Optional[str] = None):
        """Clear benchmark data"""
        with self._benchmark_lock:
            if operation:
                self._benchmark_results.pop(operation, None)
                self._performance_profiles.pop(operation, None)
                self.logger.info(f"Cleared benchmark data for {operation}")
            else:
                self._benchmark_results.clear()
                self._performance_profiles.clear()
                self.logger.info("Cleared all benchmark data")


class BenchmarkContext:
    """Context for benchmark execution"""
    
    def __init__(self, name: str, iterations: int, track_memory: bool, 
                 track_cpu: bool, benchmarks: PerformanceBenchmarks):
        self.name = name
        self.iterations = iterations
        self.track_memory = track_memory
        self.track_cpu = track_cpu
        self.benchmarks = benchmarks
        
        self.start_time = 0
        self.initial_memory = None
        self.errors = 0
        
    def __enter__(self):
        self.start_time = time.time()
        
        if self.track_memory:
            self.initial_memory = self.benchmarks.memory_optimizer.get_memory_usage()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Get final memory usage
        final_memory = None
        memory_delta = 0
        
        if self.track_memory:
            final_memory = self.benchmarks.memory_optimizer.get_memory_usage()
            memory_delta = final_memory['rss_mb'] - self.initial_memory['rss_mb']
        
        # Count errors
        error_rate = self.errors / max(1, self.iterations)
        
        # Create benchmark result
        result = BenchmarkResult(
            name=self.name,
            duration=duration,
            memory_usage_mb=final_memory['rss_mb'] if final_memory else 0,
            memory_delta_mb=memory_delta,
            iterations=self.iterations,
            error_rate=error_rate
        )
        
        # Record the result
        self.benchmarks.record_benchmark(result)
    
    def record_error(self):
        """Record an error during benchmark execution"""
        self.errors += 1


# Global performance benchmarks instance
_performance_benchmarks = None


def get_performance_benchmarks() -> PerformanceBenchmarks:
    """Get global performance benchmarks instance"""
    global _performance_benchmarks
    if _performance_benchmarks is None:
        _performance_benchmarks = PerformanceBenchmarks()
    return _performance_benchmarks