"""
Parallel processing utilities for BlastDock operations
"""

import os
import time
import threading
from typing import List, Dict, Any, Callable, Optional, Union, Tuple, Iterator
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, Future
from dataclasses import dataclass
from queue import Queue, Empty
import multiprocessing as mp

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingTask:
    """Task for parallel processing"""
    id: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    timeout: Optional[float] = None
    
    def __lt__(self, other):
        return self.priority < other.priority


@dataclass
class ProcessingResult:
    """Result from parallel processing"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    duration: float = 0
    worker_id: Optional[str] = None


class ParallelProcessor:
    """High-performance parallel processing system"""
    
    def __init__(self, max_threads: Optional[int] = None, max_processes: Optional[int] = None):
        """Initialize parallel processor"""
        self.logger = get_logger(__name__)
        
        # Determine optimal worker counts
        cpu_count = os.cpu_count() or 4
        self.max_threads = max_threads or min(32, cpu_count * 4)
        self.max_processes = max_processes or max(1, cpu_count - 1)
        
        # Executors
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.max_threads,
            thread_name_prefix='parallel-thread'
        )
        self._process_pool = ProcessPoolExecutor(
            max_workers=self.max_processes
        )
        
        # Task management
        self._task_counter = 0
        self._task_lock = threading.Lock()
        self._active_tasks: Dict[str, Future] = {}
        
        # Performance metrics
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_processing_time': 0,
            'thread_tasks': 0,
            'process_tasks': 0,
            'parallel_efficiency': 0,
            'queue_wait_time': 0
        }
        
        # Worker queues for advanced scheduling
        self._thread_queue = Queue()
        self._process_queue = Queue()
        self._result_queue = Queue()
        
        # Background workers
        self._workers_running = False
        self._worker_threads = []
        
        self.logger.debug(f"Parallel processor initialized: {self.max_threads} threads, {self.max_processes} processes")
    
    def submit_thread_task(self, func: Callable, *args, timeout: Optional[float] = None, 
                          priority: int = 0, **kwargs) -> str:
        """Submit a task for thread-based execution"""
        with self._task_lock:
            self._task_counter += 1
            task_id = f"thread-{self._task_counter}"
        
        task = ProcessingTask(
            id=task_id,
            function=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout
        )
        
        future = self._thread_pool.submit(self._execute_task, task)
        self._active_tasks[task_id] = future
        
        self.logger.debug(f"Submitted thread task: {task_id}")
        return task_id
    
    def submit_process_task(self, func: Callable, *args, timeout: Optional[float] = None,
                           priority: int = 0, **kwargs) -> str:
        """Submit a task for process-based execution"""
        with self._task_lock:
            self._task_counter += 1
            task_id = f"process-{self._task_counter}"
        
        # Process tasks need to be pickleable
        try:
            import pickle
            pickle.dumps((func, args, kwargs))
        except Exception as e:
            raise ValueError(f"Task not pickleable for process execution: {e}")
        
        task = ProcessingTask(
            id=task_id,
            function=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout
        )
        
        future = self._process_pool.submit(self._execute_task, task)
        self._active_tasks[task_id] = future
        
        self.logger.debug(f"Submitted process task: {task_id}")
        return task_id
    
    def submit_batch_threads(self, tasks: List[Tuple[Callable, tuple, dict]], 
                           timeout: Optional[float] = None) -> List[str]:
        """Submit multiple tasks for thread execution"""
        task_ids = []
        
        for func, args, kwargs in tasks:
            task_id = self.submit_thread_task(func, *args, timeout=timeout, **kwargs)
            task_ids.append(task_id)
        
        return task_ids
    
    def submit_batch_processes(self, tasks: List[Tuple[Callable, tuple, dict]], 
                             timeout: Optional[float] = None) -> List[str]:
        """Submit multiple tasks for process execution"""
        task_ids = []
        
        for func, args, kwargs in tasks:
            task_id = self.submit_process_task(func, *args, timeout=timeout, **kwargs)
            task_ids.append(task_id)
        
        return task_ids
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> ProcessingResult:
        """Get result from a specific task"""
        if task_id not in self._active_tasks:
            return ProcessingResult(
                task_id=task_id,
                success=False,
                error="Task not found"
            )
        
        future = self._active_tasks[task_id]
        
        try:
            result = future.result(timeout=timeout)
            self._active_tasks.pop(task_id, None)
            return result
        except Exception as e:
            self._active_tasks.pop(task_id, None)
            return ProcessingResult(
                task_id=task_id,
                success=False,
                error=str(e)
            )
    
    def get_results(self, task_ids: List[str], timeout: Optional[float] = None) -> List[ProcessingResult]:
        """Get results from multiple tasks"""
        results = []
        
        for task_id in task_ids:
            result = self.get_result(task_id, timeout=timeout)
            results.append(result)
        
        return results
    
    def wait_for_completion(self, task_ids: List[str], timeout: Optional[float] = None) -> List[ProcessingResult]:
        """Wait for all tasks to complete and return results"""
        start_time = time.time()
        results = []
        
        # Get futures for all tasks
        futures = {}
        for task_id in task_ids:
            if task_id in self._active_tasks:
                futures[self._active_tasks[task_id]] = task_id
        
        # Wait for completion
        try:
            for future in as_completed(futures, timeout=timeout):
                task_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(ProcessingResult(
                        task_id=task_id,
                        success=False,
                        error=str(e)
                    ))
                
                # Remove from active tasks
                self._active_tasks.pop(task_id, None)
        
        except Exception as e:
            self.logger.error(f"Error waiting for task completion: {e}")
        
        # Calculate parallel efficiency
        total_time = time.time() - start_time
        task_times = sum(r.duration for r in results if r.success)
        
        if total_time > 0 and task_times > 0:
            efficiency = min(100, (task_times / total_time) * 100 / len(task_ids))
            self.metrics['parallel_efficiency'] = efficiency
        
        return results
    
    def map_threads(self, func: Callable, items: List[Any], chunksize: int = 1) -> List[Any]:
        """Map function over items using thread pool"""
        start_time = time.time()
        
        # Submit all tasks
        task_ids = []
        for item in items:
            if isinstance(item, (list, tuple)):
                task_id = self.submit_thread_task(func, *item)
            else:
                task_id = self.submit_thread_task(func, item)
            task_ids.append(task_id)
        
        # Wait for results
        results = self.wait_for_completion(task_ids)
        
        # Extract successful results in order
        ordered_results = []
        for result in results:
            if result.success:
                ordered_results.append(result.result)
            else:
                self.logger.error(f"Task failed: {result.error}")
                ordered_results.append(None)
        
        self.metrics['thread_tasks'] += len(items)
        self.metrics['total_processing_time'] += time.time() - start_time
        
        return ordered_results
    
    def map_processes(self, func: Callable, items: List[Any], chunksize: int = 1) -> List[Any]:
        """Map function over items using process pool"""
        start_time = time.time()
        
        try:
            # Use built-in map for better performance with processes
            results = list(self._process_pool.map(func, items, chunksize=chunksize))
            
            self.metrics['process_tasks'] += len(items)
            self.metrics['total_processing_time'] += time.time() - start_time
            
            return results
            
        except Exception as e:
            self.logger.error(f"Process mapping failed: {e}")
            return [None] * len(items)
    
    def parallel_filter(self, predicate: Callable, items: List[Any], 
                       use_processes: bool = False) -> List[Any]:
        """Filter items in parallel"""
        if use_processes:
            results = self.map_processes(predicate, items)
        else:
            results = self.map_threads(predicate, items)
        
        # Filter items where predicate returned True
        filtered_items = []
        for item, result in zip(items, results):
            if result is True:
                filtered_items.append(item)
        
        return filtered_items
    
    def parallel_reduce(self, func: Callable, items: List[Any], 
                       initial: Any = None, use_processes: bool = False) -> Any:
        """Reduce items in parallel using divide-and-conquer"""
        if not items:
            return initial
        
        if len(items) == 1:
            return func(initial, items[0]) if initial is not None else items[0]
        
        # Divide items into chunks
        chunk_size = max(1, len(items) // (self.max_processes if use_processes else self.max_threads))
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        # Reduce each chunk
        def reduce_chunk(chunk):
            result = initial
            for item in chunk:
                if result is None:
                    result = item
                else:
                    result = func(result, item)
            return result
        
        if use_processes:
            chunk_results = self.map_processes(reduce_chunk, chunks)
        else:
            chunk_results = self.map_threads(reduce_chunk, chunks)
        
        # Reduce the chunk results
        final_result = initial
        for chunk_result in chunk_results:
            if chunk_result is not None:
                if final_result is None:
                    final_result = chunk_result
                else:
                    final_result = func(final_result, chunk_result)
        
        return final_result
    
    def _execute_task(self, task: ProcessingTask) -> ProcessingResult:
        """Execute a single task"""
        start_time = time.time()
        worker_id = threading.current_thread().name
        
        try:
            # Execute the task function
            result = task.function(*task.args, **task.kwargs)
            
            duration = time.time() - start_time
            
            # Update metrics
            self.metrics['tasks_completed'] += 1
            
            return ProcessingResult(
                task_id=task.id,
                success=True,
                result=result,
                duration=duration,
                worker_id=worker_id
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            # Update metrics
            self.metrics['tasks_failed'] += 1
            
            self.logger.error(f"Task {task.id} failed: {error_msg}")
            
            return ProcessingResult(
                task_id=task.id,
                success=False,
                error=error_msg,
                duration=duration,
                worker_id=worker_id
            )
    
    def start_background_workers(self, thread_workers: int = 2, process_workers: int = 1):
        """Start background workers for continuous processing"""
        if self._workers_running:
            return
        
        self._workers_running = True
        
        # Start thread workers
        for i in range(thread_workers):
            worker = threading.Thread(
                target=self._thread_worker_loop,
                name=f'bg-thread-worker-{i}',
                daemon=True
            )
            worker.start()
            self._worker_threads.append(worker)
        
        # Start process workers
        for i in range(process_workers):
            worker = threading.Thread(
                target=self._process_worker_loop,
                name=f'bg-process-worker-{i}',
                daemon=True
            )
            worker.start()
            self._worker_threads.append(worker)
        
        self.logger.info(f"Started {thread_workers} thread workers and {process_workers} process workers")
    
    def stop_background_workers(self):
        """Stop background workers"""
        if not self._workers_running:
            return
        
        self._workers_running = False
        
        # Add poison pills to queues
        for _ in self._worker_threads:
            self._thread_queue.put(None)
            self._process_queue.put(None)
        
        # Wait for workers to finish
        for worker in self._worker_threads:
            worker.join(timeout=5)
        
        self._worker_threads.clear()
        self.logger.info("Background workers stopped")
    
    def _thread_worker_loop(self):
        """Background thread worker loop"""
        while self._workers_running:
            try:
                task = self._thread_queue.get(timeout=1)
                if task is None:  # Poison pill
                    break
                
                result = self._execute_task(task)
                self._result_queue.put(result)
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Thread worker error: {e}")
    
    def _process_worker_loop(self):
        """Background process worker loop"""
        while self._workers_running:
            try:
                task = self._process_queue.get(timeout=1)
                if task is None:  # Poison pill
                    break
                
                # Submit to process pool
                future = self._process_pool.submit(self._execute_task, task)
                result = future.result(timeout=300)  # 5 minute timeout
                self._result_queue.put(result)
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Process worker error: {e}")
    
    def add_background_task(self, func: Callable, *args, use_process: bool = False, 
                           priority: int = 0, **kwargs) -> str:
        """Add task to background processing queue"""
        with self._task_lock:
            self._task_counter += 1
            task_id = f"bg-{'process' if use_process else 'thread'}-{self._task_counter}"
        
        task = ProcessingTask(
            id=task_id,
            function=func,
            args=args,
            kwargs=kwargs,
            priority=priority
        )
        
        if use_process:
            self._process_queue.put(task)
        else:
            self._thread_queue.put(task)
        
        return task_id
    
    def get_background_results(self, timeout: Optional[float] = None) -> List[ProcessingResult]:
        """Get results from background processing"""
        results = []
        end_time = time.time() + (timeout or 0) if timeout else None
        
        while True:
            try:
                remaining_time = None
                if end_time:
                    remaining_time = max(0, end_time - time.time())
                    if remaining_time <= 0:
                        break
                
                result = self._result_queue.get(timeout=remaining_time or 0.1)
                results.append(result)
                
            except Empty:
                if timeout:
                    break
                else:
                    # No timeout specified, just check once
                    break
        
        return results
    
    def get_active_task_count(self) -> int:
        """Get number of active tasks"""
        return len(self._active_tasks)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task"""
        if task_id in self._active_tasks:
            future = self._active_tasks[task_id]
            success = future.cancel()
            if success:
                self._active_tasks.pop(task_id, None)
            return success
        return False
    
    def cancel_all_tasks(self) -> int:
        """Cancel all active tasks"""
        cancelled_count = 0
        
        for task_id in list(self._active_tasks.keys()):
            if self.cancel_task(task_id):
                cancelled_count += 1
        
        return cancelled_count
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        total_tasks = self.metrics['tasks_completed'] + self.metrics['tasks_failed']
        success_rate = (self.metrics['tasks_completed'] / total_tasks * 100) if total_tasks > 0 else 0
        
        avg_processing_time = (
            self.metrics['total_processing_time'] / total_tasks
            if total_tasks > 0 else 0
        )
        
        return {
            **self.metrics,
            'active_tasks': len(self._active_tasks),
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'max_threads': self.max_threads,
            'max_processes': self.max_processes,
            'workers_running': self._workers_running,
            'queue_sizes': {
                'thread_queue': self._thread_queue.qsize(),
                'process_queue': self._process_queue.qsize(),
                'result_queue': self._result_queue.qsize()
            }
        }
    
    def optimize_for_workload(self, cpu_intensive: bool = False, io_intensive: bool = False):
        """Optimize processor for specific workload characteristics"""
        cpu_count = os.cpu_count() or 4
        
        if cpu_intensive:
            # CPU-intensive workloads benefit from process parallelism
            self.max_processes = cpu_count
            self.max_threads = min(8, cpu_count)
        elif io_intensive:
            # I/O-intensive workloads benefit from thread parallelism
            self.max_threads = min(64, cpu_count * 8)
            self.max_processes = max(1, cpu_count // 2)
        else:
            # Balanced workload
            self.max_threads = min(32, cpu_count * 4)
            self.max_processes = max(1, cpu_count - 1)
        
        self.logger.info(f"Optimized for workload: threads={self.max_threads}, processes={self.max_processes}")
    
    def close(self):
        """Close parallel processor and cleanup resources"""
        # Stop background workers
        self.stop_background_workers()
        
        # Cancel active tasks
        cancelled = self.cancel_all_tasks()
        if cancelled > 0:
            self.logger.info(f"Cancelled {cancelled} active tasks")
        
        # Shutdown executors
        try:
            self._thread_pool.shutdown(wait=True, timeout=30)
            self._process_pool.shutdown(wait=True, timeout=30)
        except Exception as e:
            self.logger.error(f"Error shutting down parallel processor: {e}")
        
        self.logger.debug("Parallel processor closed")


# Global parallel processor instance
_parallel_processor = None


def get_parallel_processor() -> ParallelProcessor:
    """Get global parallel processor instance"""
    global _parallel_processor
    if _parallel_processor is None:
        _parallel_processor = ParallelProcessor()
    return _parallel_processor