"""
Optimized template caching and loading system
"""

import os
import time
import hashlib
import threading
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..utils.logging import get_logger
from .cache import get_cache_manager, cached

logger = get_logger(__name__)


class TemplateCache:
    """High-performance template caching system"""
    
    def __init__(self):
        """Initialize template cache"""
        self.logger = get_logger(__name__)
        self.cache_manager = get_cache_manager()
        
        # Template metadata cache
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._metadata_lock = threading.RLock()
        
        # File modification time tracking
        self._file_mtimes: Dict[str, float] = {}
        
        # Template dependency tracking
        self._dependencies: Dict[str, List[str]] = {}
        
        # Performance metrics
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'load_times': [],
            'parse_times': [],
            'validation_times': []
        }
        
        # Thread pool for parallel operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='template-cache')
    
    def get_template(self, template_name: str, templates_dir: str) -> Optional[Dict[str, Any]]:
        """Get template with caching"""
        cache_key = f"template:{template_name}:{hashlib.sha256(templates_dir.encode()).hexdigest()[:8]}"
        
        # Check cache first
        start_time = time.time()
        cached_template = self.cache_manager.get(cache_key)
        
        if cached_template is not None:
            # Verify template is still valid
            if self._is_template_valid(template_name, templates_dir, cached_template):
                self.metrics['cache_hits'] += 1
                self.logger.debug(f"Template cache hit: {template_name}")
                return cached_template
            else:
                # Invalidate stale cache
                self.cache_manager.delete(cache_key)
        
        # Load template
        self.metrics['cache_misses'] += 1
        template_data = self._load_template(template_name, templates_dir)
        
        if template_data:
            # Cache the template
            self.cache_manager.set(
                cache_key, 
                template_data, 
                ttl=3600,  # 1 hour TTL
                tags=['template', template_name]
            )
            
            load_time = time.time() - start_time
            self.metrics['load_times'].append(load_time)
            self.logger.debug(f"Template loaded and cached: {template_name} ({load_time:.3f}s)")
        
        return template_data
    
    def preload_templates(self, templates_dir: str) -> Dict[str, bool]:
        """Preload all templates in parallel"""
        if not os.path.exists(templates_dir):
            return {}
        
        template_names = []
        for item in os.listdir(templates_dir):
            template_path = os.path.join(templates_dir, item)
            if os.path.isdir(template_path):
                template_names.append(item)
        
        if not template_names:
            return {}
        
        self.logger.info(f"Preloading {len(template_names)} templates...")
        
        # Load templates in parallel
        results = {}
        futures = {}
        
        for template_name in template_names:
            future = self._executor.submit(self.get_template, template_name, templates_dir)
            futures[future] = template_name
        
        # Collect results
        for future in as_completed(futures, timeout=300):  # 5 minute timeout
            template_name = futures[future]
            try:
                template_data = future.result()
                results[template_name] = template_data is not None
            except Exception as e:
                self.logger.error(f"Failed to preload template {template_name}: {e}")
                results[template_name] = False
        
        successful_loads = sum(1 for success in results.values() if success)
        self.logger.info(f"Preloaded {successful_loads}/{len(template_names)} templates successfully")
        
        return results
    
    def _load_template(self, template_name: str, templates_dir: str) -> Optional[Dict[str, Any]]:
        """Load template from filesystem"""
        template_path = os.path.join(templates_dir, template_name)
        
        if not os.path.exists(template_path) or not os.path.isdir(template_path):
            return None
        
        try:
            start_time = time.time()
            
            # Load template metadata
            metadata = self._load_template_metadata(template_path)
            if not metadata:
                return None
            
            # Load template files
            template_files = self._load_template_files(template_path)
            
            # Parse and validate template
            parse_start = time.time()
            parsed_config = self._parse_template_config(template_files)
            self.metrics['parse_times'].append(time.time() - parse_start)
            
            # Validate template
            validation_start = time.time()
            validation_result = self._validate_template_fast(template_path, parsed_config)
            self.metrics['validation_times'].append(time.time() - validation_start)
            
            # Build complete template data
            template_data = {
                'name': template_name,
                'path': template_path,
                'metadata': metadata,
                'files': template_files,
                'config': parsed_config,
                'validation': validation_result,
                'loaded_at': time.time(),
                'dependencies': self._extract_dependencies(template_files)
            }
            
            # Update file modification times
            self._update_file_mtimes(template_path)
            
            return template_data
            
        except Exception as e:
            self.logger.error(f"Failed to load template {template_name}: {e}")
            return None
    
    @cached(ttl=1800, tags=['template-metadata'])  # 30 minute cache
    def _load_template_metadata(self, template_path: str) -> Optional[Dict[str, Any]]:
        """Load template metadata with caching"""
        metadata_file = os.path.join(template_path, 'blastdock.yml')
        if not os.path.exists(metadata_file):
            metadata_file = os.path.join(template_path, 'blastdock.yaml')
        
        if not os.path.exists(metadata_file):
            # Generate basic metadata
            return {
                'name': os.path.basename(template_path),
                'description': f'Template for {os.path.basename(template_path)}',
                'version': '1.0.0',
                'generated': True
            }
        
        try:
            import yaml
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f)
            return metadata or {}
        except Exception as e:
            self.logger.warning(f"Failed to load template metadata from {metadata_file}: {e}")
            return None
    
    def _load_template_files(self, template_path: str) -> Dict[str, str]:
        """Load all template files"""
        template_files = {}
        
        # Important files to load
        file_patterns = [
            'docker-compose.yml',
            'docker-compose.yaml', 
            'Dockerfile',
            '.env.example',
            'README.md',
            'blastdock.yml',
            'blastdock.yaml'
        ]
        
        for pattern in file_patterns:
            file_path = os.path.join(template_path, pattern)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template_files[pattern] = f.read()
                except Exception as e:
                    self.logger.warning(f"Failed to read template file {file_path}: {e}")
        
        return template_files
    
    def _parse_template_config(self, template_files: Dict[str, str]) -> Dict[str, Any]:
        """Parse template configuration from files"""
        config = {}
        
        # Parse docker-compose file
        compose_content = (template_files.get('docker-compose.yml') or 
                          template_files.get('docker-compose.yaml'))
        
        if compose_content:
            try:
                import yaml
                compose_config = yaml.safe_load(compose_content)
                config['compose'] = compose_config
                
                # Extract services info
                if isinstance(compose_config, dict) and 'services' in compose_config:
                    config['services'] = list(compose_config['services'].keys())
                    
                    # Extract ports
                    ports = []
                    for service_config in compose_config['services'].values():
                        if isinstance(service_config, dict) and 'ports' in service_config:
                            ports.extend(service_config['ports'])
                    config['ports'] = ports
                    
            except Exception as e:
                self.logger.warning(f"Failed to parse docker-compose config: {e}")
        
        # Parse environment file
        env_content = template_files.get('.env.example')
        if env_content:
            config['environment'] = self._parse_env_file(env_content)
        
        # Parse BlastDock metadata
        metadata_content = (template_files.get('blastdock.yml') or 
                           template_files.get('blastdock.yaml'))
        if metadata_content:
            try:
                import yaml
                metadata = yaml.safe_load(metadata_content)
                config['blastdock'] = metadata
            except Exception as e:
                self.logger.warning(f"Failed to parse blastdock metadata: {e}")
        
        return config
    
    def _parse_env_file(self, env_content: str) -> Dict[str, str]:
        """Parse environment file content"""
        env_vars = {}
        
        for line in env_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        return env_vars
    
    def _validate_template_fast(self, template_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fast template validation"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'score': 100
        }
        
        # Check required files
        required_files = ['docker-compose.yml', 'docker-compose.yaml']
        has_compose = any(os.path.exists(os.path.join(template_path, f)) for f in required_files)
        
        if not has_compose:
            validation['errors'].append('Missing docker-compose file')
            validation['valid'] = False
            validation['score'] -= 50
        
        # Check compose configuration
        compose_config = config.get('compose')
        if compose_config:
            if not isinstance(compose_config, dict):
                validation['errors'].append('Invalid docker-compose format')
                validation['score'] -= 30
            elif 'services' not in compose_config:
                validation['errors'].append('No services defined in docker-compose')
                validation['score'] -= 40
            elif not compose_config['services']:
                validation['errors'].append('Empty services section')
                validation['score'] -= 40
        
        # Check for common issues
        services = config.get('services', [])
        if len(services) > 10:
            validation['warnings'].append(f'Large number of services ({len(services)})')
            validation['score'] -= 10
        
        return validation
    
    def _extract_dependencies(self, template_files: Dict[str, str]) -> List[str]:
        """Extract template dependencies"""
        dependencies = []
        
        # Extract Docker image dependencies
        compose_content = (template_files.get('docker-compose.yml') or 
                          template_files.get('docker-compose.yaml'))
        
        if compose_content:
            try:
                import yaml
                compose_config = yaml.safe_load(compose_content)
                
                if isinstance(compose_config, dict) and 'services' in compose_config:
                    for service_config in compose_config['services'].values():
                        if isinstance(service_config, dict) and 'image' in service_config:
                            dependencies.append(service_config['image'])
                            
            except Exception:
                pass
        
        return dependencies
    
    def _update_file_mtimes(self, template_path: str):
        """Update file modification times for cache invalidation"""
        try:
            for root, dirs, files in os.walk(template_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(file_path)
                        self._file_mtimes[file_path] = mtime
                    except OSError:
                        pass
        except Exception:
            pass
    
    def _is_template_valid(self, template_name: str, templates_dir: str, 
                          cached_template: Dict[str, Any]) -> bool:
        """Check if cached template is still valid"""
        template_path = os.path.join(templates_dir, template_name)
        
        if not os.path.exists(template_path):
            return False
        
        # Check if any template files have been modified
        try:
            for root, dirs, files in os.walk(template_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        current_mtime = os.path.getmtime(file_path)
                        cached_mtime = self._file_mtimes.get(file_path, 0)
                        
                        if current_mtime > cached_mtime:
                            return False
                    except OSError:
                        return False
        except Exception:
            return False
        
        return True
    
    def invalidate_template(self, template_name: str, templates_dir: str):
        """Invalidate cached template"""
        cache_key = f"template:{template_name}:{hashlib.sha256(templates_dir.encode()).hexdigest()[:8]}"
        self.cache_manager.delete(cache_key)
        
        # Also invalidate by pattern
        self.cache_manager.invalidate_by_pattern(f"template:{template_name}:*")
        
        self.logger.debug(f"Invalidated template cache: {template_name}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get template cache statistics"""
        cache_stats = self.cache_manager.get_stats()
        
        avg_load_time = (sum(self.metrics['load_times']) / len(self.metrics['load_times']) 
                        if self.metrics['load_times'] else 0)
        avg_parse_time = (sum(self.metrics['parse_times']) / len(self.metrics['parse_times']) 
                         if self.metrics['parse_times'] else 0)
        avg_validation_time = (sum(self.metrics['validation_times']) / len(self.metrics['validation_times']) 
                              if self.metrics['validation_times'] else 0)
        
        return {
            'template_cache_hits': self.metrics['cache_hits'],
            'template_cache_misses': self.metrics['cache_misses'],
            'template_hit_rate': (self.metrics['cache_hits'] / 
                                 (self.metrics['cache_hits'] + self.metrics['cache_misses']) * 100
                                 if self.metrics['cache_hits'] + self.metrics['cache_misses'] > 0 else 0),
            'avg_load_time': avg_load_time,
            'avg_parse_time': avg_parse_time,
            'avg_validation_time': avg_validation_time,
            'templates_loaded': len(self.metrics['load_times']),
            'tracked_files': len(self._file_mtimes),
            **cache_stats
        }
    
    def optimize_memory(self):
        """Optimize memory usage"""
        # Clear old metadata cache
        with self._metadata_lock:
            self._metadata_cache.clear()
        
        # Keep only recent file modification times
        current_time = time.time()
        stale_files = [
            path for path, mtime in self._file_mtimes.items()
            if current_time - mtime > 86400  # 24 hours
        ]
        
        for path in stale_files:
            del self._file_mtimes[path]
        
        # Trigger cache cleanup
        self.cache_manager._cleanup()
        
        self.logger.debug("Template cache memory optimized")
    
    def close(self):
        """Close template cache and cleanup resources"""
        try:
            self._executor.shutdown(wait=True, timeout=10)
        except Exception as e:
            self.logger.error(f"Error shutting down template cache executor: {e}")


# Global template cache instance
_template_cache = None


def get_template_cache() -> TemplateCache:
    """Get global template cache instance"""
    global _template_cache
    if _template_cache is None:
        _template_cache = TemplateCache()
    return _template_cache