"""
Test runner script for BlastDock test suite
"""

import os
import sys
import argparse
import pytest
from pathlib import Path


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='BlastDock Test Runner')
    
    # Test selection arguments
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    # Test configuration arguments
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fast', action='store_true', help='Skip slow tests')
    parser.add_argument('--docker', action='store_true', help='Include Docker tests')
    parser.add_argument('--network', action='store_true', help='Include network tests')
    
    # Output arguments
    parser.add_argument('--html-report', help='Generate HTML coverage report to specified directory')
    parser.add_argument('--xml-report', help='Generate XML test report to specified file')
    parser.add_argument('--json-report', help='Generate JSON test report to specified file')
    
    # Filter arguments
    parser.add_argument('--filter', '-k', help='Filter tests by pattern')
    parser.add_argument('--module', '-m', help='Run tests for specific module')
    
    args = parser.parse_args()
    
    # Build pytest arguments
    pytest_args = []
    
    # Add test directories based on selection
    if args.unit:
        pytest_args.append('tests/unit')
    elif args.integration:
        pytest_args.append('tests/integration')
    elif args.performance:
        pytest_args.append('tests/performance')
    elif args.all:
        pytest_args.append('tests/')
    else:
        # Default to unit tests
        pytest_args.append('tests/unit')
    
    # Add coverage if requested
    if args.coverage:
        pytest_args.extend([
            '--cov=blastdock',
            '--cov-report=term-missing',
            '--cov-branch'
        ])
    
    # Add HTML coverage report
    if args.html_report:
        pytest_args.extend(['--cov-report=html:' + args.html_report])
    
    # Add XML test report
    if args.xml_report:
        pytest_args.extend(['--junitxml=' + args.xml_report])
    
    # Add JSON report (requires pytest-json-report)
    if args.json_report:
        pytest_args.extend(['--json-report', '--json-report-file=' + args.json_report])
    
    # Add verbosity
    if args.verbose:
        pytest_args.append('-v')
    
    # Add test markers
    markers = []
    
    if args.fast:
        markers.append('not slow')
    
    if not args.docker:
        markers.append('not docker')
    
    if not args.network:
        markers.append('not network')
    
    if markers:
        pytest_args.extend(['-m', ' and '.join(markers)])
    
    # Add filter pattern
    if args.filter:
        pytest_args.extend(['-k', args.filter])
    
    # Add module filter
    if args.module:
        if args.module == 'cli':
            pytest_args.append('tests/unit/test_cli.py')
        elif args.module == 'traefik':
            pytest_args.append('tests/unit/test_traefik.py')
        elif args.module == 'models':
            pytest_args.append('tests/unit/test_models.py')
        elif args.module == 'integration':
            pytest_args.append('tests/integration/')
        elif args.module == 'performance':
            pytest_args.append('tests/performance/')
    
    # Add additional pytest options
    pytest_args.extend([
        '--tb=short',  # Shorter traceback format
        '--strict-markers',  # Strict marker checking
        '--strict-config',  # Strict config checking
    ])
    
    print(f"Running tests with arguments: {' '.join(pytest_args)}")
    
    # Run pytest
    exit_code = pytest.main(pytest_args)
    
    return exit_code


if __name__ == '__main__':
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Add project root to Python path
    sys.path.insert(0, str(project_root))
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run tests
    exit_code = main()
    sys.exit(exit_code)