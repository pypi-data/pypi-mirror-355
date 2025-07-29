"""
Deployment process optimization for BlastDock
"""

import os
import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from queue import Queue, PriorityQueue

from ..utils.logging import get_logger
from .cache import get_cache_manager

logger = get_logger(__name__)


@dataclass
class DeploymentTask:
    """Deployment task with priority and dependencies"""
    name: str
    priority: int
    operation: str  # 'build', 'pull', 'start', 'stop', 'remove'
    dependencies: List[str]
    estimated_duration: float
    project_name: str
    service_name: Optional[str] = None
    
    def __lt__(self, other):
        return self.priority < other.priority


class DeploymentOptimizer:
    """Optimizes deployment processes for maximum performance"""
    
    def __init__(self):
        """Initialize deployment optimizer"""
        self.logger = get_logger(__name__)
        self.cache_manager = get_cache_manager()
        
        # Performance configuration
        self.max_parallel_builds = min(4, os.cpu_count() or 2)
        self.max_parallel_pulls = min(8, os.cpu_count() or 4)
        self.max_parallel_starts = min(6, os.cpu_count() or 3)
        
        # Resource pools
        self._build_executor = ThreadPoolExecutor(
            max_workers=self.max_parallel_builds, 
            thread_name_prefix='deploy-build'
        )
        self._pull_executor = ThreadPoolExecutor(
            max_workers=self.max_parallel_pulls, 
            thread_name_prefix='deploy-pull'
        )
        self._start_executor = ThreadPoolExecutor(
            max_workers=self.max_parallel_starts, 
            thread_name_prefix='deploy-start'
        )
        
        # Deployment tracking
        self._active_deployments: Dict[str, Dict[str, Any]] = {}
        self._deployment_lock = threading.RLock()
        
        # Performance metrics
        self.metrics = {
            'deployments_completed': 0,
            'total_deployment_time': 0,
            'average_deployment_time': 0,
            'builds_completed': 0,
            'pulls_completed': 0,
            'parallel_efficiency': 0,
            'cache_hit_rate': 0
        }
        
        # Deployment queue
        self._task_queue = PriorityQueue()
        self._workers_running = False
        
        self.logger.debug(f"Deployment optimizer initialized: builds={self.max_parallel_builds}, pulls={self.max_parallel_pulls}, starts={self.max_parallel_starts}")
    
    def optimize_deployment_plan(self, project_name: str, 
                                compose_config: Dict[str, Any]) -> List[DeploymentTask]:
        """Create optimized deployment plan"""
        if not isinstance(compose_config, dict) or 'services' not in compose_config:
            return []
        
        services = compose_config['services']
        tasks = []
        
        # Analyze service dependencies
        dependency_graph = self._build_dependency_graph(services)
        
        # Create tasks for each service
        for service_name, service_config in services.items():
            # Estimate task durations
            build_time = self._estimate_build_time(service_config)
            pull_time = self._estimate_pull_time(service_config)
            start_time = self._estimate_start_time(service_config)
            
            # Determine if we need to build or pull
            if 'build' in service_config:
                tasks.append(DeploymentTask(
                    name=f"build-{service_name}",
                    priority=1,  # High priority for builds
                    operation='build',
                    dependencies=dependency_graph.get(service_name, []),
                    estimated_duration=build_time,
                    project_name=project_name,
                    service_name=service_name
                ))
            elif 'image' in service_config:
                tasks.append(DeploymentTask(
                    name=f"pull-{service_name}",
                    priority=2,  # Medium priority for pulls
                    operation='pull',
                    dependencies=[],
                    estimated_duration=pull_time,
                    project_name=project_name,
                    service_name=service_name
                ))
            
            # Start task (depends on build/pull)
            start_deps = []
            if 'build' in service_config:
                start_deps.append(f"build-{service_name}")
            elif 'image' in service_config:
                start_deps.append(f"pull-{service_name}")
            
            tasks.append(DeploymentTask(
                name=f"start-{service_name}",
                priority=3,  # Lower priority for starts
                operation='start',
                dependencies=start_deps,
                estimated_duration=start_time,
                project_name=project_name,
                service_name=service_name
            ))
        
        # Sort tasks by priority and estimated duration
        tasks.sort(key=lambda t: (t.priority, t.estimated_duration))
        
        self.logger.debug(f"Created deployment plan with {len(tasks)} tasks for {project_name}")
        return tasks
    
    def execute_deployment_plan(self, tasks: List[DeploymentTask], 
                              dry_run: bool = False) -> Dict[str, Any]:
        """Execute deployment plan with optimization"""
        if not tasks:
            return {'success': True, 'duration': 0, 'tasks_completed': 0}
        
        project_name = tasks[0].project_name
        start_time = time.time()
        
        self.logger.info(f"Executing deployment plan for {project_name}: {len(tasks)} tasks")
        
        # Track deployment
        with self._deployment_lock:
            self._active_deployments[project_name] = {
                'start_time': start_time,
                'tasks': tasks,
                'completed_tasks': [],
                'failed_tasks': [],
                'status': 'running'
            }
        
        try:
            if dry_run:
                return self._simulate_deployment(tasks)
            else:
                return self._execute_deployment_real(tasks)
        
        finally:
            # Update deployment status
            with self._deployment_lock:
                if project_name in self._active_deployments:
                    self._active_deployments[project_name]['status'] = 'completed'
                    self._active_deployments[project_name]['end_time'] = time.time()
    
    def _execute_deployment_real(self, tasks: List[DeploymentTask]) -> Dict[str, Any]:
        """Execute deployment tasks in parallel"""
        start_time = time.time()
        completed_tasks = []
        failed_tasks = []
        
        # Group tasks by operation type
        build_tasks = [t for t in tasks if t.operation == 'build']
        pull_tasks = [t for t in tasks if t.operation == 'pull']
        start_tasks = [t for t in tasks if t.operation == 'start']
        
        # Execute builds and pulls in parallel first
        parallel_futures = {}
        
        # Submit build tasks
        for task in build_tasks:
            if self._can_execute_task(task, completed_tasks):
                future = self._build_executor.submit(self._execute_task, task)
                parallel_futures[future] = task
        
        # Submit pull tasks
        for task in pull_tasks:
            if self._can_execute_task(task, completed_tasks):
                future = self._pull_executor.submit(self._execute_task, task)
                parallel_futures[future] = task
        
        # Wait for builds and pulls to complete
        for future in as_completed(parallel_futures, timeout=1800):  # 30 minute timeout
            task = parallel_futures[future]
            try:
                result = future.result()
                if result['success']:
                    completed_tasks.append(task.name)
                    self.logger.debug(f"Completed task: {task.name}")
                else:
                    failed_tasks.append(task.name)
                    self.logger.error(f"Failed task: {task.name}")
            except Exception as e:
                failed_tasks.append(task.name)
                self.logger.error(f"Task {task.name} failed with exception: {e}")
        
        # Execute start tasks after builds/pulls
        start_futures = {}
        for task in start_tasks:
            if self._can_execute_task(task, completed_tasks):
                future = self._start_executor.submit(self._execute_task, task)
                start_futures[future] = task
        
        # Wait for start tasks
        for future in as_completed(start_futures, timeout=600):  # 10 minute timeout
            task = start_futures[future]
            try:
                result = future.result()
                if result['success']:
                    completed_tasks.append(task.name)
                    self.logger.debug(f"Completed task: {task.name}")
                else:
                    failed_tasks.append(task.name)
                    self.logger.error(f"Failed task: {task.name}")
            except Exception as e:
                failed_tasks.append(task.name)
                self.logger.error(f"Task {task.name} failed with exception: {e}")
        
        # Calculate results
        duration = time.time() - start_time
        success = len(failed_tasks) == 0
        
        # Update metrics
        self.metrics['deployments_completed'] += 1
        self.metrics['total_deployment_time'] += duration
        self.metrics['average_deployment_time'] = (
            self.metrics['total_deployment_time'] / self.metrics['deployments_completed']
        )
        
        return {
            'success': success,
            'duration': duration,
            'tasks_completed': len(completed_tasks),
            'tasks_failed': len(failed_tasks),
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks
        }
    
    def _simulate_deployment(self, tasks: List[DeploymentTask]) -> Dict[str, Any]:
        """Simulate deployment for dry run"""
        total_duration = 0
        
        # Simple simulation: sum of all task durations with parallel efficiency
        build_duration = sum(t.estimated_duration for t in tasks if t.operation == 'build')
        pull_duration = sum(t.estimated_duration for t in tasks if t.operation == 'pull')
        start_duration = sum(t.estimated_duration for t in tasks if t.operation == 'start')
        
        # Account for parallelization
        parallel_build_time = build_duration / self.max_parallel_builds
        parallel_pull_time = pull_duration / self.max_parallel_pulls
        parallel_start_time = start_duration / self.max_parallel_starts
        
        # Sequential phases
        total_duration = max(parallel_build_time, parallel_pull_time) + parallel_start_time
        
        return {
            'success': True,
            'duration': total_duration,
            'tasks_completed': len(tasks),
            'tasks_failed': 0,
            'simulated': True
        }
    
    def _execute_task(self, task: DeploymentTask) -> Dict[str, Any]:
        """Execute individual deployment task"""
        start_time = time.time()
        
        try:
            # Check cache first for expensive operations
            cache_key = f"task:{task.operation}:{task.project_name}:{task.service_name}"
            
            if task.operation in ['build', 'pull']:
                cached_result = self.cache_manager.get(cache_key)
                if cached_result:
                    self.logger.debug(f"Using cached result for {task.name}")
                    return cached_result
            
            # Simulate task execution (replace with actual implementation)
            time.sleep(min(task.estimated_duration, 5))  # Cap simulation time
            
            result = {
                'success': True,
                'duration': time.time() - start_time,
                'task': task.name,
                'operation': task.operation
            }
            
            # Cache successful build/pull results
            if task.operation in ['build', 'pull'] and result['success']:
                self.cache_manager.set(cache_key, result, ttl=7200, tags=['deployment'])
            
            # Update operation metrics
            if task.operation == 'build':
                self.metrics['builds_completed'] += 1
            elif task.operation == 'pull':
                self.metrics['pulls_completed'] += 1
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time,
                'task': task.name
            }
    
    def _can_execute_task(self, task: DeploymentTask, completed_tasks: List[str]) -> bool:
        """Check if task dependencies are satisfied"""
        return all(dep in completed_tasks for dep in task.dependencies)
    
    def _build_dependency_graph(self, services: Dict[str, Any]) -> Dict[str, List[str]]:
        """Build service dependency graph"""
        dependencies = {}
        
        for service_name, service_config in services.items():
            deps = []
            
            # Check depends_on
            if isinstance(service_config, dict) and 'depends_on' in service_config:
                depends_on = service_config['depends_on']
                if isinstance(depends_on, list):
                    deps.extend(depends_on)
                elif isinstance(depends_on, dict):
                    deps.extend(depends_on.keys())
            
            # Check links (legacy)
            if isinstance(service_config, dict) and 'links' in service_config:
                links = service_config['links']
                if isinstance(links, list):
                    for link in links:
                        if ':' in link:
                            deps.append(link.split(':')[0])
                        else:
                            deps.append(link)
            
            dependencies[service_name] = deps
        
        return dependencies
    
    def _estimate_build_time(self, service_config: Dict[str, Any]) -> float:
        """Estimate build time for service"""
        if 'build' not in service_config:
            return 0
        
        # Base build time
        base_time = 60  # 1 minute base
        
        # Adjust based on build context
        build_config = service_config['build']
        if isinstance(build_config, dict):
            dockerfile = build_config.get('dockerfile', 'Dockerfile')
            
            # Estimate based on dockerfile complexity
            if dockerfile == 'Dockerfile':
                base_time = 90  # Standard dockerfile
            elif 'slim' in dockerfile.lower() or 'alpine' in dockerfile.lower():
                base_time = 45  # Lightweight image
            elif 'dev' in dockerfile.lower() or 'development' in dockerfile.lower():
                base_time = 120  # Development image with tools
        
        return base_time
    
    def _estimate_pull_time(self, service_config: Dict[str, Any]) -> float:
        """Estimate pull time for service"""
        if 'image' not in service_config:
            return 0
        
        image = service_config['image']
        
        # Base pull time
        base_time = 30  # 30 seconds base
        
        # Adjust based on image characteristics
        if ':latest' in image:
            base_time = 45  # Latest tags may be larger/change frequently
        elif 'alpine' in image:
            base_time = 15  # Alpine images are smaller
        elif any(keyword in image for keyword in ['ubuntu', 'debian', 'centos']):
            base_time = 60  # Full OS images are larger
        elif any(keyword in image for keyword in ['postgres', 'mysql', 'mongo']):
            base_time = 90  # Database images are typically large
        
        return base_time
    
    def _estimate_start_time(self, service_config: Dict[str, Any]) -> float:
        """Estimate start time for service"""
        base_time = 10  # 10 seconds base
        
        # Adjust based on service characteristics
        if isinstance(service_config, dict):
            # Health checks increase start time
            if 'healthcheck' in service_config:
                base_time += 20
            
            # Complex environment setup
            env_vars = service_config.get('environment', [])
            if len(env_vars) > 10:
                base_time += 10
            
            # Volume mounts
            volumes = service_config.get('volumes', [])
            if len(volumes) > 5:
                base_time += 15
        
        return base_time
    
    def get_deployment_status(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get current deployment status"""
        with self._deployment_lock:
            return self._active_deployments.get(project_name)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get deployment performance metrics"""
        cache_stats = self.cache_manager.get_stats()
        
        return {
            **self.metrics,
            'cache_hit_rate': cache_stats.get('hit_rate', 0),
            'active_deployments': len(self._active_deployments),
            'max_parallel_builds': self.max_parallel_builds,
            'max_parallel_pulls': self.max_parallel_pulls,
            'max_parallel_starts': self.max_parallel_starts
        }
    
    def optimize_for_system(self):
        """Optimize settings based on system resources"""
        cpu_count = os.cpu_count() or 2
        
        # Adjust parallelism based on CPU cores
        self.max_parallel_builds = min(4, max(1, cpu_count // 2))
        self.max_parallel_pulls = min(8, cpu_count)
        self.max_parallel_starts = min(6, max(2, cpu_count - 1))
        
        # Recreate thread pools with new limits
        self._build_executor.shutdown(wait=False)
        self._pull_executor.shutdown(wait=False)
        self._start_executor.shutdown(wait=False)
        
        self._build_executor = ThreadPoolExecutor(
            max_workers=self.max_parallel_builds, 
            thread_name_prefix='deploy-build'
        )
        self._pull_executor = ThreadPoolExecutor(
            max_workers=self.max_parallel_pulls, 
            thread_name_prefix='deploy-pull'
        )
        self._start_executor = ThreadPoolExecutor(
            max_workers=self.max_parallel_starts, 
            thread_name_prefix='deploy-start'
        )
        
        self.logger.info(f"Optimized deployment parallelism: builds={self.max_parallel_builds}, pulls={self.max_parallel_pulls}, starts={self.max_parallel_starts}")
    
    def close(self):
        """Close deployment optimizer and cleanup resources"""
        try:
            self._build_executor.shutdown(wait=True, timeout=30)
            self._pull_executor.shutdown(wait=True, timeout=30)
            self._start_executor.shutdown(wait=True, timeout=30)
        except Exception as e:
            self.logger.error(f"Error shutting down deployment optimizer: {e}")


# Global deployment optimizer instance
_deployment_optimizer = None


def get_deployment_optimizer() -> DeploymentOptimizer:
    """Get global deployment optimizer instance"""
    global _deployment_optimizer
    if _deployment_optimizer is None:
        _deployment_optimizer = DeploymentOptimizer()
    return _deployment_optimizer