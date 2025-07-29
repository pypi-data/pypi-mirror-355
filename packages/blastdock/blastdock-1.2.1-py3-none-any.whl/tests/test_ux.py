#!/usr/bin/env python3
"""
Tests for enhanced UX utilities and CLI decorators
"""

import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

from blastdock.utils.ux import (
    UXManager, TaskType, EnhancedProgress, TaskController,
    get_ux_manager, show_success, show_warning, show_error,
    task_progress, status_spinner
)
from blastdock.utils.cli_decorators import (
    enhanced_command, with_progress, with_spinner, 
    interactive_command, deployment_command, template_command,
    health_check_command, ProgressSteps, multi_step_operation
)


class TestUXManager:
    """Test UX manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.console_mock = MagicMock()
        self.ux_manager = UXManager(console=self.console_mock)
    
    def test_init(self):
        """Test UX manager initialization"""
        assert self.ux_manager.console == self.console_mock
        assert self.ux_manager.show_timestamps is True
        assert self.ux_manager.show_progress_bars is True
        assert self.ux_manager.animation_speed == "normal"
        assert self.ux_manager.color_theme == "auto"
    
    def test_show_welcome(self):
        """Test welcome message display"""
        self.ux_manager.show_welcome("1.0.5")
        self.console_mock.print.assert_called()
        
        # Check that print was called with a Panel object
        call_args = self.console_mock.print.call_args_list
        assert len(call_args) >= 1
    
    def test_show_success(self):
        """Test success message display"""
        details = ["Detail 1", "Detail 2"]
        self.ux_manager.show_success("Test success", details)
        self.console_mock.print.assert_called()
    
    def test_show_warning(self):
        """Test warning message display"""
        suggestions = ["Suggestion 1", "Suggestion 2"]
        self.ux_manager.show_warning("Test warning", suggestions)
        self.console_mock.print.assert_called()
    
    def test_show_error(self):
        """Test error message display"""
        suggestions = ["Fix 1", "Fix 2"]
        self.ux_manager.show_error("Test error", "Error details", suggestions)
        self.console_mock.print.assert_called()
    
    def test_show_info(self):
        """Test info display"""
        data = {"key1": "value1", "key2": "value2"}
        highlight_keys = ["key1"]
        self.ux_manager.show_info("Test Info", data, highlight_keys)
        self.console_mock.print.assert_called()
    
    def test_create_status_table(self):
        """Test status table creation"""
        headers = ["Name", "Status", "Type"]
        rows = [["Item1", "Active", "Service"], ["Item2", "Inactive", "Worker"]]
        styles = ["cyan", "green", "blue"]
        
        table = self.ux_manager.create_status_table("Test Table", headers, rows, styles)
        
        # Check that table was created (basic verification)
        assert table.title == "Test Table"
    
    @patch('blastdock.utils.ux.Prompt.ask')
    def test_prompt_choice(self, mock_ask):
        """Test choice prompt"""
        mock_ask.return_value = "option1"
        choices = ["option1", "option2", "option3"]
        
        result = self.ux_manager.prompt_choice("Choose option", choices, "option1")
        
        assert result == "option1"
        mock_ask.assert_called_once()
    
    @patch('blastdock.utils.ux.Confirm.ask')
    def test_prompt_confirm(self, mock_confirm):
        """Test confirmation prompt"""
        mock_confirm.return_value = True
        
        result = self.ux_manager.prompt_confirm("Continue?", True)
        
        assert result is True
        mock_confirm.assert_called_once()


class TestEnhancedProgress:
    """Test enhanced progress functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.console_mock = MagicMock()
        self.progress = EnhancedProgress(console=self.console_mock)
    
    def test_init(self):
        """Test enhanced progress initialization"""
        assert self.progress.console == self.console_mock
        assert self.progress._tasks == {}
        assert self.progress._progress_instances == {}
    
    def test_task_context_manager(self):
        """Test task context manager"""        
        with self.progress.task("test_task", "Test Task", TaskType.GENERAL, 100) as controller:
            assert isinstance(controller, TaskController)
            assert "test_task" in self.progress._tasks
            
            # Test task controller properties
            assert controller.ux_task.id == "test_task"
            assert controller.ux_task.name == "Test Task"
            assert controller.ux_task.task_type == TaskType.GENERAL
            assert controller.ux_task.total == 100
        
        # Task should be removed after completion
        assert "test_task" not in self.progress._tasks
    
    def test_different_task_types(self):
        """Test different task types create different progress instances"""
        with self.progress.task("download", "Download", TaskType.DOWNLOAD, 100):
            pass
        
        with self.progress.task("build", "Build", TaskType.BUILD, 100):
            pass
        
        with self.progress.task("deploy", "Deploy", TaskType.DEPLOYMENT, 100):
            pass
        
        # Should have created different progress instances
        assert TaskType.DOWNLOAD in self.progress._progress_instances
        assert TaskType.BUILD in self.progress._progress_instances
        assert TaskType.DEPLOYMENT in self.progress._progress_instances


class TestTaskController:
    """Test task controller functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        from blastdock.utils.ux import UXTask
        self.ux_task = UXTask("test", "Test Task", TaskType.GENERAL, 100)
        self.progress_mock = MagicMock()
        self.controller = TaskController(self.ux_task, self.progress_mock, "task_id", None)
    
    def test_update(self):
        """Test task progress update"""
        initial_progress = self.ux_task.progress
        
        self.controller.update(25, "Working...")
        
        assert self.ux_task.progress == initial_progress + 25
        assert self.ux_task.description == "Working..."
        self.progress_mock.update.assert_called_once()
    
    def test_set_total(self):
        """Test setting task total"""
        self.controller.set_total(200)
        
        assert self.ux_task.total == 200
        self.progress_mock.update.assert_called_with("task_id", total=200)
    
    def test_complete(self):
        """Test task completion"""
        self.ux_task.progress = 50
        self.ux_task.total = 100
        
        self.controller.complete("Finished!")
        
        assert self.ux_task.status == "completed"
        assert self.ux_task.completed_at is not None
        assert self.ux_task.description == "Finished!"
    
    def test_fail(self):
        """Test task failure"""
        self.controller.fail("Something went wrong")
        
        assert self.ux_task.status == "failed"
        assert self.ux_task.metadata['error'] == "Something went wrong"
        assert self.ux_task.completed_at is not None


class TestProgressSteps:
    """Test multi-step progress functionality"""
    
    def test_progress_steps_context_manager(self):
        """Test progress steps context manager"""
        steps = ["Step 1", "Step 2", "Step 3"]
        
        with ProgressSteps(steps, TaskType.BUILD) as progress_steps:
            assert progress_steps.total_steps == 3
            assert progress_steps.current_step == 0
            
            progress_steps.next_step("Starting step 1")
            assert progress_steps.current_step == 1
            
            progress_steps.next_step("Starting step 2")
            assert progress_steps.current_step == 2
            
            progress_steps.update_current_step("Working on step 2", 50)
            assert progress_steps.current_step == 2
    
    def test_get_current_step_name(self):
        """Test getting current step name"""
        steps = ["Step 1", "Step 2", "Step 3"]
        
        with ProgressSteps(steps) as progress_steps:
            assert progress_steps.get_current_step_name() == "Step 1"
            
            progress_steps.next_step()
            assert progress_steps.get_current_step_name() == "Step 2"


class TestCLIDecorators:
    """Test CLI decorators functionality"""
    
    def test_enhanced_command_decorator(self):
        """Test enhanced command decorator"""
        @enhanced_command(show_welcome=True, track_time=True)
        def test_command():
            return "success"
        
        result = test_command()
        assert result == "success"
    
    def test_with_progress_decorator(self):
        """Test with_progress decorator"""
        @with_progress("Test Operation", TaskType.GENERAL)
        def test_operation(_progress=None):
            assert _progress is not None
            _progress.update(50, "Working...")
            return "done"
        
        result = test_operation()
        assert result == "done"
    
    def test_with_spinner_decorator(self):
        """Test with_spinner decorator"""
        @with_spinner("Loading...", "dots")
        def test_spinner_operation(_status=None):
            assert _status is not None
            return "loaded"
        
        result = test_spinner_operation()
        assert result == "loaded"
    
    def test_deployment_command_decorator(self):
        """Test deployment command decorator"""
        @deployment_command()
        def test_deploy(project_name):
            return f"deployed {project_name}"
        
        result = test_deploy("test-project")
        assert result == "deployed test-project"
    
    def test_template_command_decorator(self):
        """Test template command decorator"""
        @template_command()
        def test_template():
            return "template operation"
        
        result = test_template()
        assert result == "template operation"
    
    def test_health_check_command_decorator(self):
        """Test health check command decorator"""
        @health_check_command()
        def test_health_check(_progress=None):
            assert _progress is not None
            return "healthy"
        
        result = test_health_check()
        assert result == "healthy"
    
    def test_multi_step_operation_decorator(self):
        """Test multi-step operation decorator"""
        steps = ["Initialize", "Process", "Finalize"]
        
        @multi_step_operation(steps, TaskType.BUILD)
        def test_multi_step(_steps=None):
            assert _steps is not None
            _steps.next_step("Starting initialization")
            _steps.next_step("Processing data")
            _steps.next_step("Finalizing")
            return "completed"
        
        result = test_multi_step()
        assert result == "completed"
    
    @patch('blastdock.utils.ux.Confirm.ask')
    def test_interactive_command_decorator(self, mock_confirm):
        """Test interactive command decorator with confirmation"""
        mock_confirm.return_value = True
        
        @interactive_command(confirm_destructive=True)
        def test_remove_command():
            return "removed"
        
        # Test that destructive operations prompt for confirmation
        result = test_remove_command()
        assert result == "removed"
        mock_confirm.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @patch('blastdock.utils.ux.get_ux_manager')
    def test_show_success_function(self, mock_get_ux):
        """Test show_success convenience function"""
        mock_ux = MagicMock()
        mock_get_ux.return_value = mock_ux
        
        show_success("Test success", ["Detail 1"])
        
        mock_ux.show_success.assert_called_once_with("Test success", ["Detail 1"])
    
    @patch('blastdock.utils.ux.get_ux_manager')
    def test_show_warning_function(self, mock_get_ux):
        """Test show_warning convenience function"""
        mock_ux = MagicMock()
        mock_get_ux.return_value = mock_ux
        
        show_warning("Test warning", ["Suggestion 1"])
        
        mock_ux.show_warning.assert_called_once_with("Test warning", ["Suggestion 1"])
    
    @patch('blastdock.utils.ux.get_ux_manager')
    def test_show_error_function(self, mock_get_ux):
        """Test show_error convenience function"""
        mock_ux = MagicMock()
        mock_get_ux.return_value = mock_ux
        
        show_error("Test error", "Details", ["Fix 1"])
        
        mock_ux.show_error.assert_called_once_with("Test error", "Details", ["Fix 1"])
    
    def test_task_progress_context_manager(self):
        """Test task_progress convenience context manager"""
        with task_progress("test", "Test Task", TaskType.GENERAL, 100) as controller:
            assert controller is not None
            controller.update(50, "Working...")
    
    def test_status_spinner_context_manager(self):
        """Test status_spinner convenience context manager"""
        with status_spinner("Loading...", "dots") as status:
            assert status is not None


class TestGlobalUXManager:
    """Test global UX manager instance"""
    
    def test_get_ux_manager_singleton(self):
        """Test that get_ux_manager returns the same instance"""
        ux1 = get_ux_manager()
        ux2 = get_ux_manager()
        
        assert ux1 is ux2
        assert isinstance(ux1, UXManager)


class TestDeploymentProgressController:
    """Test deployment-specific progress controller"""
    
    def setup_method(self):
        """Setup test environment"""
        from blastdock.utils.ux import DeploymentProgressController
        from rich.progress import Progress
        from rich.console import Console
        
        self.console = Console()
        self.progress = Progress(console=self.console)
        self.services = ["web", "db", "cache"]
        
        with self.progress:
            self.controller = DeploymentProgressController(
                self.progress, self.services, self.console
            )
    
    def test_init(self):
        """Test deployment progress controller initialization"""
        assert self.controller.services == self.services
        assert len(self.controller.service_tasks) == len(self.services)
    
    def test_update_service(self):
        """Test updating service progress"""
        self.controller.update_service("web", 50, "Building")
        # Should not raise any exceptions
    
    def test_complete_service(self):
        """Test completing service deployment"""
        self.controller.complete_service("web", True)
        self.controller.complete_service("db", False)
        # Should not raise any exceptions


class TestErrorHandlingInDecorators:
    """Test error handling in decorators"""
    
    def test_enhanced_command_exception_handling(self):
        """Test that enhanced_command handles exceptions properly"""
        @enhanced_command()
        def failing_command():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_command()
    
    def test_deployment_command_exception_handling(self):
        """Test that deployment_command handles exceptions properly"""
        @deployment_command()
        def failing_deployment():
            raise RuntimeError("Deployment failed")
        
        with pytest.raises(RuntimeError):
            failing_deployment()
    
    def test_template_command_exception_handling(self):
        """Test that template_command handles exceptions properly"""
        @template_command()
        def failing_template():
            raise FileNotFoundError("Template not found")
        
        with pytest.raises(FileNotFoundError):
            failing_template()


if __name__ == '__main__':
    pytest.main([__file__])