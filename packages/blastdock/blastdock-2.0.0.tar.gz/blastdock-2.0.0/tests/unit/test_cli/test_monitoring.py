"""Comprehensive tests for CLI monitoring module."""

import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

from blastdock.cli.monitoring import (
    monitoring, health, metrics, alerts, dashboard, logs
)
from blastdock.monitoring.health_checker import HealthStatus
from blastdock.monitoring.alert_manager import AlertSeverity


class TestMonitoringCLI:
    """Test suite for monitoring CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_health_checker(self):
        """Create mock health checker."""
        checker = Mock()
        checker.check_project_health.return_value = {
            'overall_status': HealthStatus.HEALTHY.value,
            'message': 'All services healthy',
            'duration_ms': 150.5,
            'services': {
                'web': {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'Service is running',
                    'response_time_ms': 45.2
                },
                'db': {
                    'status': HealthStatus.DEGRADED.value,
                    'message': 'High latency detected',
                    'response_time_ms': 250.8
                }
            }
        }
        return checker

    @pytest.fixture
    def mock_metrics_collector(self):
        """Create mock metrics collector."""
        collector = Mock()
        collector.get_project_metrics.return_value = {
            'cpu_usage': 45.5,
            'memory_usage': 67.8,
            'disk_usage': 23.1,
            'network_io': {'in': 1024, 'out': 2048},
            'uptime': 86400,
            'container_count': 3
        }
        collector.get_historical_metrics.return_value = [
            {'timestamp': '2023-01-01T12:00:00Z', 'cpu': 40.0, 'memory': 60.0},
            {'timestamp': '2023-01-01T12:05:00Z', 'cpu': 45.0, 'memory': 65.0}
        ]
        return collector

    @pytest.fixture
    def mock_alert_manager(self):
        """Create mock alert manager."""
        manager = Mock()
        manager.get_active_alerts.return_value = [
            {
                'id': 'alert-1',
                'rule_name': 'high_cpu',
                'severity': AlertSeverity.WARNING.value,
                'message': 'CPU usage is high',
                'timestamp': '2023-01-01T12:00:00Z',
                'project': 'test-project'
            }
        ]
        manager.get_alert_history.return_value = [
            {
                'id': 'alert-2',
                'rule_name': 'memory_leak',
                'severity': AlertSeverity.CRITICAL.value,
                'message': 'Memory leak detected',
                'timestamp': '2023-01-01T11:00:00Z',
                'resolved_at': '2023-01-01T11:30:00Z'
            }
        ]
        return manager

    @pytest.fixture
    def mock_dashboard(self):
        """Create mock monitoring dashboard."""
        dashboard = Mock()
        dashboard.start_server.return_value = True
        dashboard.stop_server.return_value = True
        dashboard.is_running.return_value = False
        dashboard.get_server_info.return_value = {
            'host': '127.0.0.1',
            'port': 8080,
            'running': False
        }
        return dashboard

    @pytest.fixture
    def mock_log_analyzer(self):
        """Create mock log analyzer."""
        analyzer = Mock()
        analyzer.analyze_project_logs.return_value = {
            'total_entries': 1000,
            'error_count': 5,
            'warning_count': 25,
            'patterns': {
                'errors': ['Connection timeout', 'Database error'],
                'warnings': ['Deprecated API', 'Slow query']
            },
            'timeline': [
                {'hour': '12:00', 'errors': 2, 'warnings': 10},
                {'hour': '13:00', 'errors': 3, 'warnings': 15}
            ]
        }
        return analyzer

    def test_monitoring_group(self, runner):
        """Test monitoring command group."""
        result = runner.invoke(monitoring, ['--help'])
        
        assert result.exit_code == 0
        assert 'Advanced monitoring and health check commands' in result.output

    def test_health_command_success(self, runner, mock_health_checker):
        """Test health command with successful check."""
        with patch('blastdock.cli.monitoring.get_health_checker', return_value=mock_health_checker):
            result = runner.invoke(health, ['test-project'])
            
            assert result.exit_code == 0
            assert 'Health Check: test-project' in result.output
            mock_health_checker.check_project_health.assert_called_once_with('test-project')

    def test_health_command_json_format(self, runner, mock_health_checker):
        """Test health command with JSON output format."""
        with patch('blastdock.cli.monitoring.get_health_checker', return_value=mock_health_checker):
            result = runner.invoke(health, ['test-project', '--format', 'json'])
            
            assert result.exit_code == 0
            # Verify JSON output is present
            assert '{' in result.output
            mock_health_checker.check_project_health.assert_called_once_with('test-project')

    def test_health_command_detailed(self, runner, mock_health_checker):
        """Test health command with detailed flag."""
        with patch('blastdock.cli.monitoring.get_health_checker', return_value=mock_health_checker):
            result = runner.invoke(health, ['test-project', '--detailed'])
            
            assert result.exit_code == 0
            mock_health_checker.check_project_health.assert_called_once_with('test-project')

    def test_health_command_unhealthy_status(self, runner, mock_health_checker):
        """Test health command with unhealthy status."""
        mock_health_checker.check_project_health.return_value = {
            'overall_status': HealthStatus.UNHEALTHY.value,
            'message': 'Services are down',
            'duration_ms': 500.0,
            'services': {
                'web': {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'Service not responding',
                    'response_time_ms': 0
                }
            }
        }
        
        with patch('blastdock.cli.monitoring.get_health_checker', return_value=mock_health_checker):
            result = runner.invoke(health, ['test-project'])
            
            assert result.exit_code == 0
            assert 'Health Check: test-project' in result.output

    def test_health_command_unknown_status(self, runner, mock_health_checker):
        """Test health command with unknown status."""
        mock_health_checker.check_project_health.return_value = {
            'overall_status': 'unknown',
            'message': 'Status unknown',
            'duration_ms': 100.0,
            'services': {}
        }
        
        with patch('blastdock.cli.monitoring.get_health_checker', return_value=mock_health_checker):
            result = runner.invoke(health, ['test-project'])
            
            assert result.exit_code == 0

    def test_metrics_command_current(self, runner, mock_metrics_collector):
        """Test metrics command for current metrics."""
        with patch('blastdock.cli.monitoring.get_metrics_collector', return_value=mock_metrics_collector):
            result = runner.invoke(metrics, ['test-project'])
            
            assert result.exit_code == 0
            assert 'Current Metrics: test-project' in result.output
            mock_metrics_collector.get_project_metrics.assert_called_once_with('test-project')

    def test_metrics_command_historical(self, runner, mock_metrics_collector):
        """Test metrics command for historical data."""
        with patch('blastdock.cli.monitoring.get_metrics_collector', return_value=mock_metrics_collector):
            result = runner.invoke(metrics, ['test-project', '--historical', '--hours', '24'])
            
            assert result.exit_code == 0
            mock_metrics_collector.get_historical_metrics.assert_called_once()

    def test_metrics_command_json_format(self, runner, mock_metrics_collector):
        """Test metrics command with JSON output."""
        with patch('blastdock.cli.monitoring.get_metrics_collector', return_value=mock_metrics_collector):
            result = runner.invoke(metrics, ['test-project', '--format', 'json'])
            
            assert result.exit_code == 0
            assert '{' in result.output

    def test_metrics_command_save_report(self, runner, mock_metrics_collector):
        """Test metrics command with report saving."""
        with patch('blastdock.cli.monitoring.get_metrics_collector', return_value=mock_metrics_collector):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as report_file:
                result = runner.invoke(metrics, [
                    'test-project',
                    '--save-report', report_file.name
                ])
                
                assert result.exit_code == 0
                assert 'Metrics report saved' in result.output

    def test_alerts_command_list(self, runner, mock_alert_manager):
        """Test alerts command to list active alerts."""
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['list'])
            
            assert result.exit_code == 0
            assert 'Active Alerts' in result.output
            mock_alert_manager.get_active_alerts.assert_called_once()

    def test_alerts_command_list_project_filter(self, runner, mock_alert_manager):
        """Test alerts command with project filter."""
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['list', '--project', 'test-project'])
            
            assert result.exit_code == 0
            mock_alert_manager.get_active_alerts.assert_called()

    def test_alerts_command_list_severity_filter(self, runner, mock_alert_manager):
        """Test alerts command with severity filter."""
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['list', '--severity', 'critical'])
            
            assert result.exit_code == 0

    def test_alerts_command_history(self, runner, mock_alert_manager):
        """Test alerts command to show history."""
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['history'])
            
            assert result.exit_code == 0
            assert 'Alert History' in result.output
            mock_alert_manager.get_alert_history.assert_called_once()

    def test_alerts_command_history_with_days(self, runner, mock_alert_manager):
        """Test alerts command history with days filter."""
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['history', '--days', '7'])
            
            assert result.exit_code == 0
            mock_alert_manager.get_alert_history.assert_called()

    def test_alerts_command_create_rule(self, runner, mock_alert_manager):
        """Test alerts command to create alert rule."""
        mock_alert_manager.create_alert_rule.return_value = True
        
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, [
                'create-rule',
                '--name', 'test-rule',
                '--condition', 'cpu > 80',
                '--severity', 'warning',
                '--project', 'test-project'
            ])
            
            assert result.exit_code == 0
            assert 'Alert rule created successfully' in result.output
            mock_alert_manager.create_alert_rule.assert_called_once()

    def test_alerts_command_delete_rule(self, runner, mock_alert_manager):
        """Test alerts command to delete alert rule."""
        mock_alert_manager.delete_alert_rule.return_value = True
        
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['delete-rule', 'test-rule'])
            
            assert result.exit_code == 0
            assert 'Alert rule deleted successfully' in result.output
            mock_alert_manager.delete_alert_rule.assert_called_once_with('test-rule')

    def test_alerts_command_delete_rule_not_found(self, runner, mock_alert_manager):
        """Test alerts command delete rule when rule not found."""
        mock_alert_manager.delete_alert_rule.return_value = False
        
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['delete-rule', 'nonexistent'])
            
            assert result.exit_code == 0
            assert 'Alert rule not found' in result.output

    def test_dashboard_command_start(self, runner, mock_dashboard):
        """Test dashboard command to start server."""
        with patch('blastdock.cli.monitoring.get_monitoring_dashboard', return_value=mock_dashboard):
            result = runner.invoke(dashboard, ['start'])
            
            assert result.exit_code == 0
            assert 'Dashboard started' in result.output
            mock_dashboard.start_server.assert_called_once()

    def test_dashboard_command_start_with_options(self, runner, mock_dashboard):
        """Test dashboard command start with custom host and port."""
        with patch('blastdock.cli.monitoring.get_monitoring_dashboard', return_value=mock_dashboard):
            result = runner.invoke(dashboard, [
                'start',
                '--host', '0.0.0.0',
                '--port', '9090'
            ])
            
            assert result.exit_code == 0
            mock_dashboard.start_server.assert_called()

    def test_dashboard_command_start_failure(self, runner, mock_dashboard):
        """Test dashboard command start failure."""
        mock_dashboard.start_server.return_value = False
        
        with patch('blastdock.cli.monitoring.get_monitoring_dashboard', return_value=mock_dashboard):
            result = runner.invoke(dashboard, ['start'])
            
            assert result.exit_code == 0
            assert 'Failed to start dashboard' in result.output

    def test_dashboard_command_stop(self, runner, mock_dashboard):
        """Test dashboard command to stop server."""
        with patch('blastdock.cli.monitoring.get_monitoring_dashboard', return_value=mock_dashboard):
            result = runner.invoke(dashboard, ['stop'])
            
            assert result.exit_code == 0
            assert 'Dashboard stopped' in result.output
            mock_dashboard.stop_server.assert_called_once()

    def test_dashboard_command_status(self, runner, mock_dashboard):
        """Test dashboard command to show status."""
        with patch('blastdock.cli.monitoring.get_monitoring_dashboard', return_value=mock_dashboard):
            result = runner.invoke(dashboard, ['status'])
            
            assert result.exit_code == 0
            assert 'Dashboard Status' in result.output
            mock_dashboard.get_server_info.assert_called_once()

    def test_dashboard_command_status_running(self, runner, mock_dashboard):
        """Test dashboard command status when running."""
        mock_dashboard.is_running.return_value = True
        mock_dashboard.get_server_info.return_value = {
            'host': '127.0.0.1',
            'port': 8080,
            'running': True
        }
        
        with patch('blastdock.cli.monitoring.get_monitoring_dashboard', return_value=mock_dashboard):
            result = runner.invoke(dashboard, ['status'])
            
            assert result.exit_code == 0
            assert 'Running' in result.output

    def test_logs_command_analyze(self, runner, mock_log_analyzer):
        """Test logs command to analyze project logs."""
        with patch('blastdock.cli.monitoring.get_log_analyzer', return_value=mock_log_analyzer):
            result = runner.invoke(logs, ['analyze', 'test-project'])
            
            assert result.exit_code == 0
            assert 'Log Analysis: test-project' in result.output
            mock_log_analyzer.analyze_project_logs.assert_called_once_with('test-project')

    def test_logs_command_analyze_with_hours(self, runner, mock_log_analyzer):
        """Test logs command analyze with hours filter."""
        with patch('blastdock.cli.monitoring.get_log_analyzer', return_value=mock_log_analyzer):
            result = runner.invoke(logs, ['analyze', 'test-project', '--hours', '24'])
            
            assert result.exit_code == 0
            mock_log_analyzer.analyze_project_logs.assert_called()

    def test_logs_command_analyze_json_format(self, runner, mock_log_analyzer):
        """Test logs command with JSON output."""
        with patch('blastdock.cli.monitoring.get_log_analyzer', return_value=mock_log_analyzer):
            result = runner.invoke(logs, ['analyze', 'test-project', '--format', 'json'])
            
            assert result.exit_code == 0
            assert '{' in result.output

    def test_logs_command_analyze_save_report(self, runner, mock_log_analyzer):
        """Test logs command with report saving."""
        with patch('blastdock.cli.monitoring.get_log_analyzer', return_value=mock_log_analyzer):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as report_file:
                result = runner.invoke(logs, [
                    'analyze', 'test-project',
                    '--save-report', report_file.name
                ])
                
                assert result.exit_code == 0
                assert 'Log analysis saved' in result.output

    def test_logs_command_tail(self, runner):
        """Test logs command to tail logs."""
        with patch('blastdock.cli.monitoring.get_log_analyzer') as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.tail_project_logs.return_value = True
            mock_get_analyzer.return_value = mock_analyzer
            
            result = runner.invoke(logs, ['tail', 'test-project'])
            
            assert result.exit_code == 0
            mock_analyzer.tail_project_logs.assert_called_once()

    def test_logs_command_tail_with_lines(self, runner):
        """Test logs command tail with lines parameter."""
        with patch('blastdock.cli.monitoring.get_log_analyzer') as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.tail_project_logs.return_value = True
            mock_get_analyzer.return_value = mock_analyzer
            
            result = runner.invoke(logs, ['tail', 'test-project', '--lines', '100'])
            
            assert result.exit_code == 0

    def test_logs_command_search(self, runner):
        """Test logs command to search logs."""
        with patch('blastdock.cli.monitoring.get_log_analyzer') as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.search_project_logs.return_value = [
                {'timestamp': '2023-01-01T12:00:00Z', 'level': 'ERROR', 'message': 'Test error'},
                {'timestamp': '2023-01-01T12:01:00Z', 'level': 'ERROR', 'message': 'Another error'}
            ]
            mock_get_analyzer.return_value = mock_analyzer
            
            result = runner.invoke(logs, ['search', 'test-project', '--pattern', 'error'])
            
            assert result.exit_code == 0
            mock_analyzer.search_project_logs.assert_called_once()

    def test_logs_command_search_no_results(self, runner):
        """Test logs command search with no results."""
        with patch('blastdock.cli.monitoring.get_log_analyzer') as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.search_project_logs.return_value = []
            mock_get_analyzer.return_value = mock_analyzer
            
            result = runner.invoke(logs, ['search', 'test-project', '--pattern', 'nonexistent'])
            
            assert result.exit_code == 0
            assert 'No log entries found' in result.output

    def test_metrics_command_error_handling(self, runner, mock_metrics_collector):
        """Test metrics command error handling."""
        mock_metrics_collector.get_project_metrics.side_effect = Exception("Metrics collection failed")
        
        with patch('blastdock.cli.monitoring.get_metrics_collector', return_value=mock_metrics_collector):
            result = runner.invoke(metrics, ['test-project'])
            
            assert result.exit_code == 0
            assert 'Error collecting metrics' in result.output

    def test_health_command_no_services(self, runner, mock_health_checker):
        """Test health command when no services are found."""
        mock_health_checker.check_project_health.return_value = {
            'overall_status': HealthStatus.HEALTHY.value,
            'message': 'No services found',
            'duration_ms': 50.0,
            'services': {}
        }
        
        with patch('blastdock.cli.monitoring.get_health_checker', return_value=mock_health_checker):
            result = runner.invoke(health, ['empty-project'])
            
            assert result.exit_code == 0

    def test_alerts_command_no_active_alerts(self, runner, mock_alert_manager):
        """Test alerts command when no active alerts exist."""
        mock_alert_manager.get_active_alerts.return_value = []
        
        with patch('blastdock.cli.monitoring.get_alert_manager', return_value=mock_alert_manager):
            result = runner.invoke(alerts, ['list'])
            
            assert result.exit_code == 0
            assert 'No active alerts' in result.output