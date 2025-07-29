"""
Enhanced Docker utility functions for BlastDock
Now uses the new comprehensive Docker integration modules
"""

import logging
from typing import Dict, List, Optional, Any, Iterator

from .logging import get_logger
from ..docker import (
    get_docker_client, DockerClient, ComposeManager, ContainerManager,
    ImageManager, NetworkManager, VolumeManager, DockerHealthChecker
)
from ..docker.errors import DockerError, DockerNotFoundError, DockerNotRunningError

logger = get_logger(__name__)


class EnhancedDockerClient:
    """Enhanced Docker client with comprehensive functionality"""
    
    def __init__(self):
        """Initialize enhanced Docker client"""
        self._docker_client = get_docker_client()
        self._compose_manager = ComposeManager()
        self._container_manager = ContainerManager()
        self._image_manager = ImageManager()
        self._network_manager = NetworkManager()
        self._volume_manager = VolumeManager()
        self._health_checker = DockerHealthChecker()
        self.logger = get_logger(__name__)
    
    def is_docker_running(self) -> bool:
        """Check if Docker daemon is running"""
        try:
            availability = self._docker_client.check_docker_availability()
            return availability['docker_running']
        except Exception:
            return False
    
    def is_docker_available(self) -> bool:
        """Check if Docker is available"""
        try:
            availability = self._docker_client.check_docker_availability()
            return availability['docker_available']
        except Exception:
            return False
    
    def compose_up(self, project_path: str, project_name: Optional[str] = None) -> tuple[bool, str]:
        """Run docker compose up"""
        try:
            compose_file = self._compose_manager.find_compose_file(project_path)
            if not compose_file:
                return False, "No compose file found in project directory"
            
            self._compose_manager.project_dir = project_path
            self._compose_manager.project_name = project_name
            
            result = self._compose_manager.start_services(compose_file=compose_file)
            
            if result['success']:
                return True, f"Services started successfully in {result['startup_time']:.1f} seconds"
            else:
                return False, f"Failed to start services: {'; '.join(result['errors'])}"
                
        except Exception as e:
            self.logger.error(f"Compose up failed: {e}")
            return False, str(e)
    
    def compose_down(self, project_path: str, project_name: Optional[str] = None) -> tuple[bool, str]:
        """Run docker compose down"""
        try:
            compose_file = self._compose_manager.find_compose_file(project_path)
            if not compose_file:
                return False, "No compose file found in project directory"
            
            self._compose_manager.project_dir = project_path
            self._compose_manager.project_name = project_name
            
            result = self._compose_manager.stop_services(compose_file=compose_file)
            
            if result['success']:
                return True, f"Services stopped successfully in {result['stop_time']:.1f} seconds"
            else:
                return False, f"Failed to stop services: {'; '.join(result['errors'])}"
                
        except Exception as e:
            self.logger.error(f"Compose down failed: {e}")
            return False, str(e)
    
    def compose_down_with_volumes(self, project_path: str, project_name: Optional[str] = None) -> tuple[bool, str]:
        """Run docker compose down with volume removal"""
        try:
            compose_file = self._compose_manager.find_compose_file(project_path)
            if not compose_file:
                return False, "No compose file found in project directory"
            
            self._compose_manager.project_dir = project_path
            self._compose_manager.project_name = project_name
            
            result = self._compose_manager.remove_services(volumes=True, compose_file=compose_file)
            
            if result['success']:
                return True, f"Services and volumes removed successfully in {result['remove_time']:.1f} seconds"
            else:
                return False, f"Failed to remove services: {'; '.join(result['errors'])}"
                
        except Exception as e:
            self.logger.error(f"Compose down with volumes failed: {e}")
            return False, str(e)
    
    def compose_logs(self, project_path: str, project_name: Optional[str] = None, 
                    service: Optional[str] = None, follow: bool = False) -> tuple[bool, str]:
        """Get docker compose logs"""
        try:
            compose_file = self._compose_manager.find_compose_file(project_path)
            if not compose_file:
                return False, "No compose file found in project directory"
            
            self._compose_manager.project_dir = project_path
            self._compose_manager.project_name = project_name
            
            logs = self._compose_manager.get_service_logs(
                service=service, 
                follow=follow,
                compose_file=compose_file
            )
            
            return True, logs
            
        except Exception as e:
            self.logger.error(f"Compose logs failed: {e}")
            return False, str(e)
    
    def get_container_status(self, project_name: str) -> List[Dict[str, Any]]:
        """Get status of containers for a project"""
        try:
            # Get all containers and filter by project
            containers = self._container_manager.list_containers(all_containers=True)
            
            project_containers = []
            for container in containers:
                container_name = container.get('Names', '')
                # Check if container belongs to this project (basic heuristic)
                if project_name in container_name or f"{project_name}_" in container_name:
                    try:
                        detailed_info = self._container_manager.get_container_info(container_name)
                        project_containers.append({
                            'name': detailed_info['name'],
                            'status': detailed_info['state'].get('Status', 'unknown'),
                            'image': detailed_info['image'],
                            'ports': detailed_info.get('host_config', {}).get('PortBindings', {})
                        })
                    except Exception as e:
                        self.logger.warning(f"Could not get info for container {container_name}: {e}")
                        project_containers.append({
                            'name': container_name,
                            'status': container.get('State', 'unknown'),
                            'image': container.get('Image', 'unknown'),
                            'ports': {}
                        })
            
            return project_containers
            
        except Exception as e:
            self.logger.error(f"Error getting container status: {e}")
            return []
    
    def get_container_logs(self, container_name: str, tail: int = 100, follow: bool = False) -> str | Iterator[str]:
        """Get logs from a specific container"""
        try:
            if follow:
                # Note: This is a simplified implementation for compatibility
                # Full streaming would require additional handling
                logs = self._container_manager.get_container_logs(container_name, tail=tail)
                return iter(logs.split('\n')) if logs else iter([])
            else:
                return self._container_manager.get_container_logs(container_name, tail=tail) or ""
                
        except Exception as e:
            self.logger.error(f"Error getting container logs: {e}")
            return f"Error: {str(e)}"
    
    def list_containers(self, all: bool = True) -> List[Dict[str, Any]]:
        """List Docker containers"""
        try:
            containers = self._container_manager.list_containers(all_containers=all)
            
            formatted_containers = []
            for container in containers:
                # Get detailed info for each container
                try:
                    detailed_info = self._container_manager.get_container_info(container.get('Names', ''))
                    formatted_containers.append({
                        'id': detailed_info['id'],
                        'name': detailed_info['name'],
                        'image': detailed_info['image'],
                        'status': detailed_info['state'].get('Status', 'unknown'),
                        'state': detailed_info['state'].get('Status', 'unknown'),
                        'created': detailed_info['created'],
                        'ports': detailed_info.get('host_config', {}).get('PortBindings', {}),
                        'labels': detailed_info.get('config', {}).get('Labels', {})
                    })
                except Exception:
                    # Fallback to basic info
                    formatted_containers.append({
                        'id': container.get('ID', '')[:12],
                        'name': container.get('Names', ''),
                        'image': container.get('Image', ''),
                        'status': container.get('State', 'unknown'),
                        'state': container.get('State', 'unknown'),
                        'created': container.get('CreatedAt', ''),
                        'ports': {},
                        'labels': {}
                    })
            
            return formatted_containers
            
        except Exception as e:
            self.logger.error(f"Error listing containers: {e}")
            return []
    
    def get_container_info(self, container_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed container information"""
        try:
            detailed_info = self._container_manager.get_container_info(container_name)
            
            return {
                'id': detailed_info['id'],
                'name': detailed_info['name'],
                'image': detailed_info['image'],
                'status': detailed_info['state'].get('Status', 'unknown'),
                'state': detailed_info['state'].get('Status', 'unknown'),
                'created': detailed_info['created'],
                'ports': detailed_info.get('host_config', {}).get('PortBindings', {}),
                'labels': detailed_info.get('config', {}).get('Labels', {}),
                'network_settings': detailed_info.get('network_settings', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error getting container info: {e}")
            return None
    
    def list_networks(self) -> List[Dict[str, Any]]:
        """List Docker networks"""
        try:
            networks = self._network_manager.list_networks()
            
            formatted_networks = []
            for network in networks:
                # Get detailed info for each network
                try:
                    detailed_info = self._network_manager.get_network_info(network.get('Name', ''))
                    formatted_networks.append({
                        'id': detailed_info['id'],
                        'name': detailed_info['name'],
                        'driver': detailed_info['driver'],
                        'scope': detailed_info['scope']
                    })
                except Exception:
                    # Fallback to basic info
                    formatted_networks.append({
                        'id': network.get('ID', '')[:12],
                        'name': network.get('Name', ''),
                        'driver': network.get('Driver', 'unknown'),
                        'scope': network.get('Scope', 'unknown')
                    })
            
            return formatted_networks
            
        except Exception as e:
            self.logger.error(f"Error listing networks: {e}")
            return []
    
    def create_network(self, name: str, driver: str = 'bridge', attachable: bool = False):
        """Create Docker network"""
        try:
            result = self._network_manager.create_network(
                name=name,
                driver=driver,
                attachable=attachable
            )
            
            if result['success']:
                self.logger.info(f"Created network: {name}")
                return result['network_id']
            else:
                raise Exception(f"Failed to create network: {'; '.join(result['errors'])}")
                
        except Exception as e:
            self.logger.error(f"Error creating network {name}: {e}")
            raise
    
    def remove_network(self, name: str) -> bool:
        """Remove Docker network"""
        try:
            result = self._network_manager.remove_network(name)
            
            if result['success']:
                self.logger.info(f"Removed network: {name}")
                return True
            else:
                self.logger.error(f"Failed to remove network {name}: {'; '.join(result['errors'])}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing network {name}: {e}")
            return False
    
    def restart_container(self, container_name: str) -> bool:
        """Restart a container"""
        try:
            result = self._container_manager.restart_container(container_name)
            
            if result['success']:
                self.logger.info(f"Restarted container: {container_name}")
                return True
            else:
                self.logger.error(f"Failed to restart container {container_name}: {'; '.join(result['errors'])}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting container {container_name}: {e}")
            return False
    
    def stop_container(self, container_name: str) -> bool:
        """Stop a container"""
        try:
            result = self._container_manager.stop_container(container_name)
            
            if result['success']:
                self.logger.info(f"Stopped container: {container_name}")
                return True
            else:
                self.logger.error(f"Failed to stop container {container_name}: {'; '.join(result['errors'])}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping container {container_name}: {e}")
            return False
    
    def start_container(self, container_name: str) -> bool:
        """Start a container"""
        try:
            result = self._container_manager.start_container(container_name)
            
            if result['success']:
                self.logger.info(f"Started container: {container_name}")
                return True
            else:
                self.logger.error(f"Failed to start container {container_name}: {'; '.join(result['errors'])}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting container {container_name}: {e}")
            return False
    
    def remove_container(self, container_name: str, force: bool = False) -> bool:
        """Remove a container"""
        try:
            result = self._container_manager.remove_container(container_name, force=force)
            
            if result['success']:
                self.logger.info(f"Removed container: {container_name}")
                return True
            else:
                self.logger.error(f"Failed to remove container {container_name}: {'; '.join(result['errors'])}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing container {container_name}: {e}")
            return False
    
    def get_docker_info(self) -> Optional[Dict[str, Any]]:
        """Get Docker system information"""
        try:
            return self._docker_client.get_system_info()
        except Exception as e:
            self.logger.error(f"Error getting Docker info: {e}")
            return None
    
    def check_compose_version(self) -> tuple[bool, str]:
        """Check if Docker Compose is available"""
        try:
            availability = self._docker_client.check_docker_availability()
            
            if availability['docker_compose_available']:
                version = availability.get('docker_compose_version', 'unknown')
                return True, f"Docker Compose version {version}"
            else:
                return False, "Docker Compose not found"
                
        except Exception as e:
            return False, f"Error checking Docker Compose: {str(e)}"
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive Docker environment health summary"""
        try:
            return self._health_checker.get_health_summary()
        except Exception as e:
            self.logger.error(f"Error getting health summary: {e}")
            return {
                'overall_healthy': False,
                'error': str(e)
            }


# Legacy compatibility class (maintains old interface)
DockerClient = EnhancedDockerClient