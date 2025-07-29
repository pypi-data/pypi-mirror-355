#!/usr/bin/env python3
"""
BlastDock CLI - Enhanced Docker Deployment CLI Tool
Main CLI interface for managing Docker application deployments
"""

import sys
import os
import signal
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import version and system info
from ._version import __version__, get_system_info, check_python_version

# Import core modules
from .core.template_manager import TemplateManager
from .core.deployment_manager import DeploymentManager
from .core.monitor import Monitor
from .core.config import get_config_manager, get_config

# Import utilities
from .utils.logging import get_logger, initialize_logging, log_exception
from .utils.filesystem import paths, initialize_directories
from .utils.validators import InputValidator

# Import exceptions
from .exceptions import (
    BlastDockError, TemplateNotFoundError, ProjectNotFoundError,
    ConfigurationError, ValidationError
)

# Initialize console
console = Console()

# Global logger (will be initialized in CLI setup)
logger = None


def signal_handler(signum, frame):
    """Handle keyboard interrupt signals gracefully"""
    console.print("\n[yellow]Operation cancelled by user[/yellow]")
    sys.exit(130)  # Standard exit code for SIGINT


# Set up signal handlers
signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)


def setup_cli_environment(verbose: bool = False, quiet: bool = False, 
                         log_level: str = None, profile: str = "default"):
    """Setup CLI environment with logging and configuration"""
    global logger
    
    # Determine log level
    if log_level:
        level = log_level.upper()
    elif verbose:
        level = "DEBUG"
    elif quiet:
        level = "ERROR"
    else:
        level = "INFO"
    
    # Initialize logging
    initialize_logging(
        log_level=level,
        log_to_console=not quiet,
        log_to_file=True
    )
    
    # Get logger
    logger = get_logger("cli")
    
    # Initialize directories
    try:
        initialize_directories()
    except Exception as e:
        logger.error(f"Failed to initialize directories: {e}")
        if not quiet:
            console.print(f"[yellow]Warning: Could not initialize directories: {e}[/yellow]")
    
    # Load configuration
    try:
        config_manager = get_config_manager(profile)
        config = config_manager.config
        logger.debug(f"Loaded configuration for profile '{profile}'")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        if not quiet:
            console.print(f"[yellow]Warning: Could not load configuration: {e}[/yellow]")


def handle_exception(e: Exception, command: str = "command"):
    """Centralized exception handling"""
    if isinstance(e, BlastDockError):
        logger.error(f"{command} failed: {e}")
        console.print(f"[red]Error: {e}[/red]")
        if isinstance(e, (TemplateNotFoundError, ProjectNotFoundError)):
            sys.exit(2)  # Not found
        else:
            sys.exit(1)  # General error
    else:
        logger.error(f"Unexpected error in {command}: {e}", exc_info=True)
        console.print(f"[red]Unexpected error: {e}[/red]")
        console.print("[dim]Check logs for more details[/dim]")
        sys.exit(1)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-error output')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              help='Set logging level')
@click.option('--profile', default='default', help='Configuration profile to use')
@click.version_option(version=__version__, prog_name='BlastDock')
@click.pass_context
def cli(ctx, verbose, quiet, log_level, profile):
    """BlastDock - Docker Deployment CLI Tool
    
    Simplify Docker application deployment with pre-built templates.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store options in context
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    ctx.obj['log_level'] = log_level
    ctx.obj['profile'] = profile
    
    # Setup environment
    setup_cli_environment(verbose, quiet, log_level, profile)
    
    # Check Python version
    if not check_python_version():
        console.print("[red]Error: BlastDock requires Python 3.8 or higher[/red]")
        sys.exit(1)


@cli.command()
@click.argument('template_name')
@click.option('--interactive', '-i', is_flag=True, help='Interactive configuration mode')
@click.option('--name', help='Project name (skip prompt)')
@click.pass_context
def init(ctx, template_name, interactive, name):
    """Initialize a new deployment from a template"""
    try:
        template_manager = TemplateManager()
        
        # Validate template exists
        if not template_manager.template_exists(template_name):
            available_templates = template_manager.list_templates()
            console.print(f"[red]Template '{template_name}' not found![/red]")
            
            if available_templates:
                console.print("\n[bold]Available templates:[/bold]")
                for template in available_templates:
                    info = template_manager.get_template_info(template)
                    description = info.get('description', 'No description')
                    console.print(f"  [cyan]{template}[/cyan] - {description}")
            else:
                console.print("[yellow]No templates available[/yellow]")
            
            raise TemplateNotFoundError(template_name)
        
        # Get project name
        if name:
            project_name = name
        else:
            project_name = click.prompt("Enter project name", type=str)
        
        # Validate project name
        is_valid, error = InputValidator.validate_project_name(project_name)
        if not is_valid:
            raise ValidationError(f"Invalid project name: {error}")
        
        # Get configuration
        if interactive:
            console.print(f"[bold]Configuring {template_name} template...[/bold]")
            config = template_manager.interactive_config(template_name)
        else:
            config = template_manager.get_default_config(template_name)
        
        # Create deployment
        deployment_manager = DeploymentManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Creating project '{project_name}'...", total=None)
            deployment_manager.create_deployment(project_name, template_name, config)
        
        # Success message
        console.print(f"[green]✓ Successfully created project '{project_name}'[/green]")
        console.print(f"[dim]Location: {paths.get_project_path(project_name)}[/dim]")
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  blastdock deploy {project_name}")
        
        logger.info(f"Successfully initialized project '{project_name}' with template '{template_name}'")
        
    except (KeyboardInterrupt, click.exceptions.Abort, EOFError):
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        handle_exception(e, "init")


@cli.command()
@click.argument('project_name')
@click.option('--force', '-f', is_flag=True, help='Force deployment without confirmation')
@click.pass_context
def deploy(ctx, project_name, force):
    """Deploy an application"""
    try:
        deployment_manager = DeploymentManager()
        
        # Check if project exists
        if not deployment_manager.project_exists(project_name):
            available_projects = deployment_manager.list_projects()
            console.print(f"[red]Project '{project_name}' not found![/red]")
            
            if available_projects:
                console.print("\n[bold]Available projects:[/bold]")
                for project in available_projects[:5]:  # Show first 5
                    console.print(f"  [cyan]{project}[/cyan]")
                if len(available_projects) > 5:
                    console.print(f"  [dim]... and {len(available_projects) - 5} more[/dim]")
            
            raise ProjectNotFoundError(project_name)
        
        # Get configuration for confirmation prompts
        config_manager = get_config_manager(ctx.obj['profile'])
        
        # Confirmation prompt
        if not force and config_manager.should_confirm_destructive_operations():
            if not click.confirm(f"Deploy project '{project_name}'?"):
                console.print("[yellow]Deployment cancelled[/yellow]")
                return
        
        # Deploy with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Deploying '{project_name}'...", total=None)
            deployment_manager.deploy(project_name)
        
        # Success message
        console.print(f"[green]✓ Successfully deployed '{project_name}'[/green]")
        
        # Show status
        monitor = Monitor()
        status = monitor.get_status(project_name)
        console.print(f"[dim]Status: {status}[/dim]")
        
        logger.info(f"Successfully deployed project '{project_name}'")
        
    except (KeyboardInterrupt, click.exceptions.Abort, EOFError):
        console.print("\n[yellow]Deployment cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        handle_exception(e, "deploy")


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), 
              default='table', help='Output format')
@click.pass_context
def list(ctx, output_format):
    """List all deployments"""
    try:
        deployment_manager = DeploymentManager()
        projects = deployment_manager.list_projects()
        
        if not projects:
            console.print("[yellow]No deployments found[/yellow]")
            console.print("[dim]Use 'blastdock init <template>' to create your first deployment[/dim]")
            return
        
        if output_format == 'json':
            import json
            project_data = []
            monitor = Monitor()
            
            for project in projects:
                try:
                    status = monitor.get_status(project)
                    template = deployment_manager.get_project_template(project)
                    created = deployment_manager.get_project_created_date(project)
                    
                    project_data.append({
                        'name': project,
                        'status': status,
                        'template': template,
                        'created': created
                    })
                except Exception as e:
                    logger.warning(f"Failed to get info for project {project}: {e}")
                    project_data.append({
                        'name': project,
                        'status': 'unknown',
                        'template': 'unknown',
                        'created': 'unknown'
                    })
            
            console.print(json.dumps(project_data, indent=2))
        else:
            # Table format
            table = Table(title="BlastDock Deployments")
            table.add_column("Project Name", style="cyan", no_wrap=True)
            table.add_column("Status", style="green")
            table.add_column("Template", style="blue")
            table.add_column("Created", style="magenta")
            
            monitor = Monitor()
            for project in projects:
                try:
                    status = monitor.get_status(project)
                    template = deployment_manager.get_project_template(project)
                    created = deployment_manager.get_project_created_date(project)
                    
                    # Color code status
                    if status.lower() in ['running', 'up']:
                        status_display = f"[green]{status}[/green]"
                    elif status.lower() in ['stopped', 'down']:
                        status_display = f"[red]{status}[/red]"
                    else:
                        status_display = f"[yellow]{status}[/yellow]"
                    
                    table.add_row(project, status_display, template, created)
                except Exception as e:
                    logger.warning(f"Failed to get info for project {project}: {e}")
                    table.add_row(project, "[red]error[/red]", "unknown", "unknown")
            
            console.print(table)
        
        logger.debug(f"Listed {len(projects)} projects")
        
    except Exception as e:
        handle_exception(e, "list")


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), 
              default='table', help='Output format')
@click.pass_context
def templates(ctx, output_format):
    """List available templates"""
    try:
        template_manager = TemplateManager()
        available_templates = template_manager.list_templates()
        
        if not available_templates:
            console.print("[yellow]No templates available[/yellow]")
            return
        
        if output_format == 'json':
            import json
            template_data = []
            
            for template in available_templates:
                try:
                    info = template_manager.get_template_info(template)
                    template_data.append({
                        'name': template,
                        'description': info.get('description', 'No description'),
                        'version': info.get('version', 'unknown'),
                        'services': info.get('services', [])
                    })
                except Exception as e:
                    logger.warning(f"Failed to get info for template {template}: {e}")
                    template_data.append({
                        'name': template,
                        'description': 'Error loading template info',
                        'version': 'unknown',
                        'services': []
                    })
            
            console.print(json.dumps(template_data, indent=2))
        else:
            # Table format
            table = Table(title="Available Templates")
            table.add_column("Template", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            table.add_column("Services", style="blue")
            table.add_column("Version", style="magenta")
            
            for template in available_templates:
                try:
                    info = template_manager.get_template_info(template)
                    description = info.get('description', 'No description')
                    version = info.get('version', 'unknown')
                    services = ', '.join(info.get('services', []))
                    
                    table.add_row(template, description, services, version)
                except Exception as e:
                    logger.warning(f"Failed to get info for template {template}: {e}")
                    table.add_row(template, "Error loading template info", "", "unknown")
            
            console.print(table)
        
        logger.debug(f"Listed {len(available_templates)} templates")
        
    except Exception as e:
        handle_exception(e, "templates")


@cli.command()
@click.argument('project_name')
@click.pass_context 
def status(ctx, project_name):
    """Check deployment status"""
    try:
        deployment_manager = DeploymentManager()
        
        if not deployment_manager.project_exists(project_name):
            raise ProjectNotFoundError(project_name)
        
        monitor = Monitor()
        status_text = monitor.get_detailed_status(project_name)
        
        # Display the status (it's already a Rich Text object with formatting)
        console.print(Panel(
            status_text,
            title=f"Status: {project_name}",
            border_style="blue"
        ))
        
        logger.debug(f"Retrieved status for project '{project_name}'")
        
    except Exception as e:
        handle_exception(e, "status")


@cli.command()
@click.argument('project_name')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--service', '-s', help='Show logs for specific service')
@click.option('--tail', type=int, default=50, help='Number of recent lines to show')
@click.pass_context
def logs(ctx, project_name, follow, service, tail):
    """View deployment logs"""
    try:
        deployment_manager = DeploymentManager()
        
        if not deployment_manager.project_exists(project_name):
            raise ProjectNotFoundError(project_name)
        
        monitor = Monitor()
        
        if follow:
            console.print(f"[dim]Following logs for '{project_name}' (Ctrl+C to stop)[/dim]")
            monitor.follow_logs(project_name, service)
        else:
            logs = monitor.get_logs(project_name, service, tail=tail)
            if logs:
                console.print(logs)
            else:
                console.print("[yellow]No logs available[/yellow]")
        
        logger.debug(f"Retrieved logs for project '{project_name}'")
        
    except (KeyboardInterrupt, click.exceptions.Abort, EOFError):
        console.print("\n[dim]Log following stopped[/dim]")
        sys.exit(130)
    except Exception as e:
        handle_exception(e, "logs")


@cli.command()
@click.argument('project_name')
@click.option('--force', '-f', is_flag=True, help='Force stop without confirmation')
@click.pass_context
def stop(ctx, project_name, force):
    """Stop a deployment"""
    try:
        deployment_manager = DeploymentManager()
        
        if not deployment_manager.project_exists(project_name):
            raise ProjectNotFoundError(project_name)
        
        # Get configuration for confirmation prompts
        config_manager = get_config_manager(ctx.obj['profile'])
        
        # Confirmation prompt
        if not force and config_manager.should_confirm_destructive_operations():
            if not click.confirm(f"Stop project '{project_name}'?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return
        
        # Stop with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Stopping '{project_name}'...", total=None)
            deployment_manager.stop(project_name)
        
        console.print(f"[green]✓ Successfully stopped '{project_name}'[/green]")
        logger.info(f"Successfully stopped project '{project_name}'")
        
    except (KeyboardInterrupt, click.exceptions.Abort, EOFError):
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        handle_exception(e, "stop")


@cli.command()
@click.argument('project_name')
@click.option('--force', '-f', is_flag=True, help='Force removal without confirmation')
@click.option('--keep-data', is_flag=True, help='Keep data volumes')
@click.pass_context
def remove(ctx, project_name, force, keep_data):
    """Remove a deployment"""
    try:
        deployment_manager = DeploymentManager()
        
        if not deployment_manager.project_exists(project_name):
            raise ProjectNotFoundError(project_name)
        
        # Get configuration for confirmation prompts
        config_manager = get_config_manager(ctx.obj['profile'])
        
        # Confirmation prompt
        if not force and config_manager.should_confirm_destructive_operations():
            console.print(f"[red]Warning: This will permanently remove '{project_name}'[/red]")
            if not keep_data:
                console.print("[red]This will also remove all data volumes![/red]")
            
            if not click.confirm(f"Remove project '{project_name}'?"):
                console.print("[yellow]Operation cancelled[/yellow]")
                return
        
        # Remove with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Removing '{project_name}'...", total=None)
            deployment_manager.remove(project_name, keep_data=keep_data)
        
        console.print(f"[green]✓ Successfully removed '{project_name}'[/green]")
        logger.info(f"Successfully removed project '{project_name}' (keep_data={keep_data})")
        
    except (KeyboardInterrupt, click.exceptions.Abort, EOFError):
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        handle_exception(e, "remove")


@cli.command()
@click.argument('project_name')
@click.pass_context
def config(ctx, project_name):
    """Show project configuration"""
    try:
        deployment_manager = DeploymentManager()
        
        if not deployment_manager.project_exists(project_name):
            raise ProjectNotFoundError(project_name)
        
        config_data = deployment_manager.get_project_config(project_name)
        
        # Create configuration panel
        panel_content = []
        
        for key, value in config_data.items():
            if isinstance(value, dict):
                panel_content.append(f"[bold]{key}:[/bold]")
                for sub_key, sub_value in value.items():
                    panel_content.append(f"  {sub_key}: {sub_value}")
            else:
                panel_content.append(f"[bold]{key}:[/bold] {value}")
        
        console.print(Panel(
            "\n".join(panel_content),
            title=f"Configuration: {project_name}",
            border_style="blue"
        ))
        
        logger.debug(f"Retrieved configuration for project '{project_name}'")
        
    except Exception as e:
        handle_exception(e, "config")


@cli.command()
@click.pass_context
def version(ctx):
    """Show version and system information"""
    try:
        system_info = get_system_info()
        
        # Create version panel
        panel_content = []
        panel_content.append(f"[bold]BlastDock Version:[/bold] {system_info['blastdock_version']}")
        panel_content.append(f"[bold]Python Version:[/bold] {system_info['python_version']}")
        panel_content.append(f"[bold]Platform:[/bold] {system_info['platform']}")
        panel_content.append(f"[bold]Architecture:[/bold] {system_info['architecture']}")
        panel_content.append(f"[bold]System:[/bold] {system_info['system']}")
        
        # Add configuration info
        try:
            config_manager = get_config_manager(ctx.obj['profile'])
            panel_content.append(f"\n[bold]Configuration Profile:[/bold] {ctx.obj['profile']}")
            panel_content.append(f"[bold]Config Directory:[/bold] {paths.config_dir}")
            panel_content.append(f"[bold]Data Directory:[/bold] {paths.data_dir}")
            panel_content.append(f"[bold]Log Directory:[/bold] {paths.log_dir}")
        except Exception:
            pass
        
        console.print(Panel(
            "\n".join(panel_content),
            title="BlastDock System Information",
            border_style="green"
        ))
        
    except Exception as e:
        handle_exception(e, "version")


def main():
    """Main entry point with global exception handling"""
    try:
        cli()
    except (KeyboardInterrupt, click.exceptions.Abort, EOFError):
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        console.print("[dim]Check logs for more details[/dim]")
        sys.exit(1)


if __name__ == '__main__':
    main()