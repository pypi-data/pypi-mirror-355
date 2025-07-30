"""
Test helper utilities
"""

import os
import tempfile
import shutil
import json
import yaml
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional, Generator, List
from unittest.mock import Mock, patch, MagicMock
import subprocess


class TempDirectory:
    """Context manager for temporary directory operations"""
    
    def __init__(self, prefix: str = "blastdock_test_"):
        self.prefix = prefix
        self.path: Optional[Path] = None
    
    def __enter__(self) -> Path:
        self.path = Path(tempfile.mkdtemp(prefix=self.prefix))
        return self.path
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path and self.path.exists():
            shutil.rmtree(self.path)


@contextmanager
def temp_compose_file(content: Dict[str, Any], filename: str = "docker-compose.yml") -> Generator[Path, None, None]:
    """Create a temporary compose file"""
    with TempDirectory() as temp_dir:
        compose_path = temp_dir / filename
        with open(compose_path, 'w') as f:
            yaml.dump(content, f)
        yield compose_path


@contextmanager
def temp_template_file(template: Dict[str, Any], name: str = "test-template.yml") -> Generator[Path, None, None]:
    """Create a temporary template file"""
    with TempDirectory() as temp_dir:
        template_path = temp_dir / name
        with open(template_path, 'w') as f:
            yaml.dump(template, f)
        yield template_path


@contextmanager
def mock_subprocess_run(return_values: List[subprocess.CompletedProcess]) -> Generator[Mock, None, None]:
    """Mock subprocess.run with specific return values"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = return_values
        yield mock_run


@contextmanager
def mock_docker_command(stdout: str = "", stderr: str = "", returncode: int = 0) -> Generator[Mock, None, None]:
    """Mock a docker command execution"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['docker', 'ps'],
            returncode=returncode,
            stdout=stdout.encode() if isinstance(stdout, str) else stdout,
            stderr=stderr.encode() if isinstance(stderr, str) else stderr
        )
        yield mock_run


class MockDockerClient:
    """Mock Docker client for testing"""
    
    def __init__(self, default_success: bool = True):
        self.default_success = default_success
        self.command_history: List[List[str]] = []
        self.responses: Dict[str, Any] = {}
    
    def execute_command(self, command: List[str]) -> Mock:
        """Execute a mocked command"""
        self.command_history.append(command)
        
        # Check for specific command responses
        command_str = ' '.join(command)
        for pattern, response in self.responses.items():
            if pattern in command_str:
                return Mock(**response)
        
        # Return default response
        if self.default_success:
            return Mock(success=True, stdout="", stderr="", exit_code=0)
        else:
            return Mock(success=False, stdout="", stderr="Command failed", exit_code=1)
    
    def set_response(self, command_pattern: str, response: Dict[str, Any]):
        """Set a specific response for a command pattern"""
        self.responses[command_pattern] = response
    
    def get_command_history(self) -> List[List[str]]:
        """Get the history of executed commands"""
        return self.command_history
    
    def reset(self):
        """Reset the mock client"""
        self.command_history.clear()
        self.responses.clear()


class FileSystemMocker:
    """Helper for mocking file system operations"""
    
    @staticmethod
    @contextmanager
    def mock_file_exists(paths: Dict[str, bool]) -> Generator[Mock, None, None]:
        """Mock os.path.exists for specific paths"""
        def exists_side_effect(path):
            return paths.get(path, False)
        
        with patch('os.path.exists', side_effect=exists_side_effect) as mock_exists:
            yield mock_exists
    
    @staticmethod
    @contextmanager
    def mock_file_read(files: Dict[str, str]) -> Generator[Mock, None, None]:
        """Mock file reading for specific files"""
        def open_side_effect(path, mode='r', **kwargs):
            if path in files and 'r' in mode:
                return MagicMock(__enter__=lambda self: MagicMock(read=lambda: files[path]))
            raise FileNotFoundError(f"No such file: {path}")
        
        with patch('builtins.open', side_effect=open_side_effect) as mock_open:
            yield mock_open
    
    @staticmethod
    @contextmanager
    def mock_directory_listing(listings: Dict[str, List[str]]) -> Generator[Mock, None, None]:
        """Mock os.listdir for specific directories"""
        def listdir_side_effect(path):
            if path in listings:
                return listings[path]
            raise FileNotFoundError(f"No such directory: {path}")
        
        with patch('os.listdir', side_effect=listdir_side_effect) as mock_listdir:
            yield mock_listdir


class CliRunner:
    """Helper for testing CLI commands"""
    
    def __init__(self):
        self.last_result: Optional[Any] = None
    
    def invoke(self, cli_func, args: List[str], catch_exceptions: bool = True, **kwargs):
        """Invoke a CLI command"""
        from click.testing import CliRunner as ClickRunner
        
        runner = ClickRunner()
        result = runner.invoke(cli_func, args, catch_exceptions=catch_exceptions, **kwargs)
        self.last_result = result
        return result
    
    def assert_success(self, message: Optional[str] = None):
        """Assert the last command succeeded"""
        assert self.last_result is not None
        assert self.last_result.exit_code == 0, f"Command failed with exit code {self.last_result.exit_code}: {self.last_result.output}"
        if message:
            assert message in self.last_result.output
    
    def assert_failure(self, exit_code: Optional[int] = None, message: Optional[str] = None):
        """Assert the last command failed"""
        assert self.last_result is not None
        assert self.last_result.exit_code != 0, "Command succeeded when it should have failed"
        if exit_code is not None:
            assert self.last_result.exit_code == exit_code
        if message:
            assert message in self.last_result.output


def create_mock_deployment(project_name: str = "test-project", 
                         status: str = "running",
                         template: str = "nginx") -> Dict[str, Any]:
    """Create a mock deployment object"""
    return {
        'project_name': project_name,
        'template': template,
        'status': status,
        'created_at': '2023-01-01T12:00:00Z',
        'containers': [
            {
                'name': f"{project_name}_web_1",
                'id': 'abc123',
                'status': status,
                'image': f'{template}:latest'
            }
        ],
        'config': {
            'port': 8080
        }
    }


def assert_docker_command_called(mock_client: Mock, command: str, times: int = 1):
    """Assert a specific docker command was called"""
    calls = [call for call in mock_client.execute_command.call_args_list 
             if command in ' '.join(call[0][0])]
    assert len(calls) == times, f"Expected '{command}' to be called {times} times, but was called {len(calls)} times"


def assert_file_created(path: Path, content_check: Optional[str] = None):
    """Assert a file was created with optional content check"""
    assert path.exists(), f"File {path} was not created"
    if content_check:
        content = path.read_text()
        assert content_check in content, f"Expected content '{content_check}' not found in {path}"


def assert_yaml_file_valid(path: Path) -> Dict[str, Any]:
    """Assert a YAML file is valid and return its content"""
    assert path.exists(), f"YAML file {path} does not exist"
    with open(path) as f:
        try:
            content = yaml.safe_load(f)
            return content
        except yaml.YAMLError as e:
            raise AssertionError(f"Invalid YAML in {path}: {e}")


def assert_json_file_valid(path: Path) -> Dict[str, Any]:
    """Assert a JSON file is valid and return its content"""
    assert path.exists(), f"JSON file {path} does not exist"
    with open(path) as f:
        try:
            content = json.load(f)
            return content
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON in {path}: {e}")


class MockTraefikIntegrator:
    """Mock Traefik integrator for testing"""
    
    def __init__(self):
        self.process_compose_called = False
        self.last_compose_data = None
        self.last_config = None
    
    def process_compose(self, compose_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock process_compose method"""
        self.process_compose_called = True
        self.last_compose_data = compose_data
        self.last_config = config
        
        # Add mock Traefik labels
        if 'services' in compose_data:
            for service_name, service in compose_data['services'].items():
                if 'labels' not in service:
                    service['labels'] = []
                service['labels'].extend([
                    f"traefik.enable=true",
                    f"traefik.http.routers.{service_name}.rule=Host(`{config.get('domain', 'example.com')}`)"
                ])
        
        return compose_data