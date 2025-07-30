"""
Comprehensive test suite for DeploymentManager
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

from blastdock.core.deployment_manager import DeploymentManager
from blastdock.utils.docker_utils import DockerClient
from blastdock.core.template_manager import TemplateManager
from blastdock.core.domain import DomainManager
from blastdock.core.traefik import TraefikIntegrator


class TestDeploymentManagerInit:
    """Test DeploymentManager initialization"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.ensure_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_initialization(self, mock_traefik, mock_domain, mock_template, mock_docker, mock_ensure_dir, mock_get_deploys_dir):
        """Test DeploymentManager proper initialization"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        manager = DeploymentManager()
        
        assert manager.deploys_dir == "/test/deploys"
        assert manager.docker_client is not None
        assert manager.template_manager is not None
        assert manager.domain_manager is not None
        assert manager.traefik_integrator is not None
        
        mock_ensure_dir.assert_called_once_with("/test/deploys")


class TestDeploymentManagerCreateDeployment:
    """Test create_deployment method"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_name = "test-project"
        self.template_name = "wordpress"
        self.config = {
            "domain": "test.local",
            "database_password": "secret123"
        }

    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.ensure_dir')
    @patch('blastdock.core.deployment_manager.load_yaml')
    @patch('blastdock.core.deployment_manager.save_yaml')
    @patch('blastdock.core.deployment_manager.save_json')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_create_deployment_success(self, mock_traefik_class, mock_domain_class, 
                                     mock_template_class, mock_docker_class,
                                     mock_save_json, mock_save_yaml, mock_load_yaml,
                                     mock_ensure_dir, mock_get_project_path, mock_get_deploys_dir):
        """Test successful deployment creation"""
        # Setup mocks
        project_path = os.path.join(self.temp_dir, self.project_name)
        mock_get_deploys_dir.return_value = self.temp_dir
        mock_get_project_path.return_value = project_path
        
        # Mock template manager
        mock_template_manager = Mock()
        mock_template_manager.templates_dir = "/templates"
        mock_template_manager.render_template.return_value = {
            'compose': {
                'version': '3.8',
                'services': {
                    'wordpress': {
                        'image': 'wordpress:latest',
                        'ports': ['80:80']
                    }
                }
            }
        }
        mock_template_class.return_value = mock_template_manager
        
        # Mock traefik integrator
        mock_traefik_integrator = Mock()
        mock_traefik_integrator.process_compose.return_value = {
            'version': '3.8',
            'services': {
                'wordpress': {
                    'image': 'wordpress:latest',
                    'ports': ['80:80'],
                    'labels': ['traefik.enable=true']
                }
            }
        }
        mock_traefik_class.return_value = mock_traefik_integrator
        
        # Mock template file loading
        mock_load_yaml.return_value = {
            'metadata': {'name': 'WordPress', 'version': '1.0'}
        }
        
        # Mock os.path.exists to return False (project doesn't exist)
        with patch('os.path.exists', return_value=False):
            manager = DeploymentManager()
            result = manager.create_deployment(self.project_name, self.template_name, self.config)
        
        # Verify project directory creation
        mock_ensure_dir.assert_any_call(project_path)
        mock_ensure_dir.assert_any_call(os.path.join(project_path, 'config'))
        mock_ensure_dir.assert_any_call(os.path.join(project_path, 'logs'))
        
        # Verify template rendering
        mock_template_manager.render_template.assert_called_once()
        
        # Verify Traefik processing
        mock_traefik_integrator.process_compose.assert_called_once()
        
        # Verify file saving
        mock_save_yaml.assert_called()
        mock_save_json.assert_called()

    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_create_deployment_project_exists(self, mock_traefik_class, mock_domain_class,
                                            mock_template_class, mock_docker_class,
                                            mock_get_deploys_dir, mock_get_project_path):
        """Test deployment creation when project already exists"""
        mock_get_deploys_dir.return_value = self.temp_dir
        mock_get_project_path.return_value = os.path.join(self.temp_dir, self.project_name)
        
        # Mock os.path.exists to return True (project exists)
        with patch('os.path.exists', return_value=True):
            manager = DeploymentManager()
            
            with pytest.raises(Exception) as exc_info:
                manager.create_deployment(self.project_name, self.template_name, self.config)
            
            assert "already exists" in str(exc_info.value)

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_create_deployment_template_error(self, mock_traefik_class, mock_domain_class,
                                            mock_template_class, mock_docker_class,
                                            mock_get_project_path, mock_get_deploys_dir):
        """Test deployment creation when template rendering fails"""
        mock_get_deploys_dir.return_value = self.temp_dir
        mock_get_project_path.return_value = os.path.join(self.temp_dir, self.project_name)
        
        # Mock template manager to raise error
        mock_template_manager = Mock()
        mock_template_manager.render_template.side_effect = Exception("Template not found")
        mock_template_class.return_value = mock_template_manager
        
        with patch('os.path.exists', return_value=False):
            with patch('blastdock.core.deployment_manager.ensure_dir'):
                manager = DeploymentManager()
                
                with pytest.raises(Exception) as exc_info:
                    manager.create_deployment(self.project_name, self.template_name, self.config)
                
                assert "Template not found" in str(exc_info.value)


class TestDeploymentManagerDeployProject:
    """Test deploy_project method"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_deploy_project_success(self, mock_traefik_class, mock_domain_class,
                                   mock_template_class, mock_docker_class,
                                   mock_get_project_path, mock_get_deploys_dir):
        """Test successful project deployment"""
        project_name = "test-project"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = f"/test/deploys/{project_name}"
        
        # Mock Docker client
        mock_docker = Mock()
        mock_docker.execute_command.return_value = {'success': True, 'output': 'Containers started'}
        mock_docker_class.return_value = mock_docker
        
        with patch('os.path.exists', return_value=True):  # Project exists
            manager = DeploymentManager()
            result = manager.deploy_project(project_name)
            
            assert result['success'] is True
            mock_docker.execute_command.assert_called()

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_deploy_project_not_found(self, mock_traefik_class, mock_domain_class,
                                     mock_template_class, mock_docker_class,
                                     mock_get_project_path, mock_get_deploys_dir):
        """Test deployment of non-existent project"""
        project_name = "nonexistent-project"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = f"/test/deploys/{project_name}"
        
        with patch('os.path.exists', return_value=False):  # Project doesn't exist
            manager = DeploymentManager()
            
            with pytest.raises(Exception) as exc_info:
                manager.deploy_project(project_name)
            
            assert "not found" in str(exc_info.value) or "does not exist" in str(exc_info.value)

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_deploy_project_docker_error(self, mock_traefik_class, mock_domain_class,
                                        mock_template_class, mock_docker_class,
                                        mock_get_project_path, mock_get_deploys_dir):
        """Test deployment with Docker command failure"""
        project_name = "test-project"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = f"/test/deploys/{project_name}"
        
        # Mock Docker client with failure
        mock_docker = Mock()
        mock_docker.execute_command.return_value = {
            'success': False, 
            'error': 'Docker daemon not running'
        }
        mock_docker_class.return_value = mock_docker
        
        with patch('os.path.exists', return_value=True):
            manager = DeploymentManager()
            result = manager.deploy_project(project_name)
            
            assert result['success'] is False
            assert 'error' in result


class TestDeploymentManagerStopProject:
    """Test stop_project method"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_stop_project_success(self, mock_traefik_class, mock_domain_class,
                                 mock_template_class, mock_docker_class,
                                 mock_get_project_path, mock_get_deploys_dir):
        """Test successful project stop"""
        project_name = "test-project"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = f"/test/deploys/{project_name}"
        
        # Mock Docker client
        mock_docker = Mock()
        mock_docker.execute_command.return_value = {'success': True, 'output': 'Containers stopped'}
        mock_docker_class.return_value = mock_docker
        
        with patch('os.path.exists', return_value=True):
            manager = DeploymentManager()
            result = manager.stop_project(project_name)
            
            assert result['success'] is True
            mock_docker.execute_command.assert_called()


class TestDeploymentManagerListProjects:
    """Test list_projects method"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_list_projects_success(self, mock_traefik_class, mock_domain_class,
                                  mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test successful project listing"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        # Mock os.listdir to return project directories
        with patch('os.listdir', return_value=['project1', 'project2', 'project3']):
            with patch('os.path.isdir', return_value=True):
                manager = DeploymentManager()
                projects = manager.list_projects()
                
                assert len(projects) == 3
                assert 'project1' in projects
                assert 'project2' in projects
                assert 'project3' in projects

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_list_projects_empty(self, mock_traefik_class, mock_domain_class,
                                mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test listing projects when none exist"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        with patch('os.listdir', return_value=[]):
            manager = DeploymentManager()
            projects = manager.list_projects()
            
            assert len(projects) == 0

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_list_projects_with_files(self, mock_traefik_class, mock_domain_class,
                                     mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test listing projects ignoring files"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        # Mock directory contents with both directories and files
        with patch('os.listdir', return_value=['project1', 'project2', 'somefile.txt', 'project3']):
            def mock_isdir(path):
                return not path.endswith('.txt')
            
            with patch('os.path.isdir', side_effect=mock_isdir):
                manager = DeploymentManager()
                projects = manager.list_projects()
                
                assert len(projects) == 3
                assert 'project1' in projects
                assert 'project2' in projects
                assert 'project3' in projects
                assert 'somefile.txt' not in projects


class TestDeploymentManagerRemoveProject:
    """Test remove_project method"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_remove_project_success(self, mock_traefik_class, mock_domain_class,
                                   mock_template_class, mock_docker_class,
                                   mock_get_project_path, mock_get_deploys_dir):
        """Test successful project removal"""
        project_name = "test-project"
        project_path = f"/test/deploys/{project_name}"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = project_path
        
        # Mock Docker client for stopping
        mock_docker = Mock()
        mock_docker.execute_command.return_value = {'success': True}
        mock_docker_class.return_value = mock_docker
        
        with patch('os.path.exists', return_value=True):
            with patch('shutil.rmtree') as mock_rmtree:
                manager = DeploymentManager()
                result = manager.remove_project(project_name)
                
                assert result['success'] is True
                mock_rmtree.assert_called_once_with(project_path)

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_remove_project_not_found(self, mock_traefik_class, mock_domain_class,
                                     mock_template_class, mock_docker_class,
                                     mock_get_project_path, mock_get_deploys_dir):
        """Test removal of non-existent project"""
        project_name = "nonexistent-project"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = f"/test/deploys/{project_name}"
        
        with patch('os.path.exists', return_value=False):
            manager = DeploymentManager()
            
            with pytest.raises(Exception) as exc_info:
                manager.remove_project(project_name)
            
            assert "not found" in str(exc_info.value) or "does not exist" in str(exc_info.value)


class TestDeploymentManagerProjectStatus:
    """Test get_project_status method"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_get_project_status_running(self, mock_traefik_class, mock_domain_class,
                                       mock_template_class, mock_docker_class,
                                       mock_get_project_path, mock_get_deploys_dir):
        """Test getting status of running project"""
        project_name = "test-project"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = f"/test/deploys/{project_name}"
        
        # Mock Docker client
        mock_docker = Mock()
        mock_docker.execute_command.return_value = {
            'success': True,
            'output': 'web_1   Up   8080->80/tcp'
        }
        mock_docker_class.return_value = mock_docker
        
        with patch('os.path.exists', return_value=True):
            manager = DeploymentManager()
            status = manager.get_project_status(project_name)
            
            assert status['project_name'] == project_name
            assert status['status'] in ['running', 'stopped', 'unknown']

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.get_project_path')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_get_project_status_not_found(self, mock_traefik_class, mock_domain_class,
                                         mock_template_class, mock_docker_class,
                                         mock_get_project_path, mock_get_deploys_dir):
        """Test getting status of non-existent project"""
        project_name = "nonexistent-project"
        mock_get_deploys_dir.return_value = "/test/deploys"
        mock_get_project_path.return_value = f"/test/deploys/{project_name}"
        
        with patch('os.path.exists', return_value=False):
            manager = DeploymentManager()
            
            with pytest.raises(Exception) as exc_info:
                manager.get_project_status(project_name)
            
            assert "not found" in str(exc_info.value) or "does not exist" in str(exc_info.value)


class TestDeploymentManagerGetConfig:
    """Test _get_config method"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_get_config_success(self, mock_traefik_class, mock_domain_class,
                               mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test successful config retrieval"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        with patch('blastdock.core.config.get_config') as mock_get_config:
            mock_config = {'setting1': 'value1', 'setting2': 'value2'}
            mock_get_config.return_value = mock_config
            
            manager = DeploymentManager()
            config = manager._get_config()
            
            assert config == mock_config
            mock_get_config.assert_called_once()

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_get_config_import_error(self, mock_traefik_class, mock_domain_class,
                                    mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test config retrieval with import error"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        with patch('blastdock.core.config.get_config', side_effect=ImportError("Config module not found")):
            manager = DeploymentManager()
            config = manager._get_config()
            
            # Should return empty dict on import error
            assert config == {}


class TestDeploymentManagerUtilityMethods:
    """Test utility methods"""

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_validate_project_name_valid(self, mock_traefik_class, mock_domain_class,
                                        mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test validation of valid project names"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        manager = DeploymentManager()
        
        valid_names = ["test-project", "my_app", "project123", "a"]
        for name in valid_names:
            assert manager.validate_project_name(name) is True

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_validate_project_name_invalid(self, mock_traefik_class, mock_domain_class,
                                          mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test validation of invalid project names"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        manager = DeploymentManager()
        
        invalid_names = ["", "project with spaces", "project/with/slashes", "project:with:colons"]
        for name in invalid_names:
            assert manager.validate_project_name(name) is False

    @patch('blastdock.core.deployment_manager.get_deploys_dir')
    @patch('blastdock.core.deployment_manager.DockerClient')
    @patch('blastdock.core.deployment_manager.TemplateManager')
    @patch('blastdock.core.deployment_manager.DomainManager')
    @patch('blastdock.core.deployment_manager.TraefikIntegrator')
    def test_get_project_info(self, mock_traefik_class, mock_domain_class,
                             mock_template_class, mock_docker_class, mock_get_deploys_dir):
        """Test getting project information"""
        mock_get_deploys_dir.return_value = "/test/deploys"
        
        with patch('blastdock.core.deployment_manager.get_project_path') as mock_get_project_path:
            with patch('blastdock.core.deployment_manager.load_json') as mock_load_json:
                project_path = "/test/deploys/test-project"
                mock_get_project_path.return_value = project_path
                
                project_info = {
                    'name': 'test-project',
                    'template': 'wordpress',
                    'created_at': '2023-01-01T12:00:00',
                    'config': {'domain': 'test.local'}
                }
                mock_load_json.return_value = project_info
                
                with patch('os.path.exists', return_value=True):
                    manager = DeploymentManager()
                    info = manager.get_project_info('test-project')
                    
                    assert info == project_info
                    mock_load_json.assert_called_once()