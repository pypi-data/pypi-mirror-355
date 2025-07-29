"""
Custom exception classes for BlastDock
"""


class BlastDockError(Exception):
    """Base exception class for all BlastDock errors"""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__


class ConfigurationError(BlastDockError):
    """Raised when there's a configuration-related error"""
    pass


class TemplateError(BlastDockError):
    """Base class for template-related errors"""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a requested template cannot be found"""
    
    def __init__(self, template_name: str):
        super().__init__(f"Template '{template_name}' not found")
        self.template_name = template_name


class TemplateValidationError(TemplateError):
    """Raised when template validation fails"""
    
    def __init__(self, template_name: str, validation_errors: list):
        errors_str = "\n".join(f"  - {error}" for error in validation_errors)
        super().__init__(f"Template '{template_name}' validation failed:\n{errors_str}")
        self.template_name = template_name
        self.validation_errors = validation_errors


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails"""
    
    def __init__(self, template_name: str, render_error: str):
        super().__init__(f"Failed to render template '{template_name}': {render_error}")
        self.template_name = template_name
        self.render_error = render_error


class ProjectError(BlastDockError):
    """Base class for project-related errors"""
    pass


class ProjectNotFoundError(ProjectError):
    """Raised when a requested project cannot be found"""
    
    def __init__(self, project_name: str):
        super().__init__(f"Project '{project_name}' not found")
        self.project_name = project_name


class ProjectAlreadyExistsError(ProjectError):
    """Raised when trying to create a project that already exists"""
    
    def __init__(self, project_name: str):
        super().__init__(f"Project '{project_name}' already exists")
        self.project_name = project_name


class ProjectConfigurationError(ProjectError):
    """Raised when project configuration is invalid"""
    
    def __init__(self, project_name: str, config_error: str):
        super().__init__(f"Configuration error in project '{project_name}': {config_error}")
        self.project_name = project_name
        self.config_error = config_error


class DeploymentError(BlastDockError):
    """Base class for deployment-related errors"""
    pass


class DeploymentFailedError(DeploymentError):
    """Raised when deployment fails"""
    
    def __init__(self, project_name: str, reason: str):
        super().__init__(f"Deployment of '{project_name}' failed: {reason}")
        self.project_name = project_name
        self.reason = reason


class DeploymentNotFoundError(DeploymentError):
    """Raised when trying to operate on a non-existent deployment"""
    
    def __init__(self, project_name: str):
        super().__init__(f"No active deployment found for project '{project_name}'")
        self.project_name = project_name


class DockerError(BlastDockError):
    """Base class for Docker-related errors"""
    pass


class DockerNotAvailableError(DockerError):
    """Raised when Docker is not available or not running"""
    
    def __init__(self, reason: str = None):
        message = "Docker is not available or not running"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.reason = reason


class DockerComposeError(DockerError):
    """Raised when Docker Compose operations fail"""
    
    def __init__(self, operation: str, project_name: str, error_output: str):
        super().__init__(f"Docker Compose {operation} failed for '{project_name}': {error_output}")
        self.operation = operation
        self.project_name = project_name
        self.error_output = error_output


class ValidationError(BlastDockError):
    """Base class for validation errors"""
    pass


class PortValidationError(ValidationError):
    """Raised when port validation fails"""
    
    def __init__(self, port: str, reason: str):
        super().__init__(f"Invalid port '{port}': {reason}")
        self.port = port
        self.reason = reason


class PortConflictError(ValidationError):
    """Raised when port conflicts are detected"""
    
    def __init__(self, port: int, conflicting_service: str = None):
        message = f"Port {port} is already in use"
        if conflicting_service:
            message += f" by {conflicting_service}"
        super().__init__(message)
        self.port = port
        self.conflicting_service = conflicting_service


class DomainValidationError(ValidationError):
    """Raised when domain validation fails"""
    
    def __init__(self, domain: str, reason: str):
        super().__init__(f"Invalid domain '{domain}': {reason}")
        self.domain = domain
        self.reason = reason


class DatabaseNameValidationError(ValidationError):
    """Raised when database name validation fails"""
    
    def __init__(self, db_name: str, reason: str):
        super().__init__(f"Invalid database name '{db_name}': {reason}")
        self.db_name = db_name
        self.reason = reason


class PasswordValidationError(ValidationError):
    """Raised when password validation fails"""
    
    def __init__(self, reason: str):
        super().__init__(f"Invalid password: {reason}")
        self.reason = reason


class FileSystemError(BlastDockError):
    """Base class for filesystem-related errors"""
    pass


class DirectoryNotWritableError(FileSystemError):
    """Raised when a required directory is not writable"""
    
    def __init__(self, directory: str):
        super().__init__(f"Directory '{directory}' is not writable")
        self.directory = directory


class InsufficientSpaceError(FileSystemError):
    """Raised when there's insufficient disk space"""
    
    def __init__(self, required_space: str, available_space: str):
        super().__init__(f"Insufficient disk space. Required: {required_space}, Available: {available_space}")
        self.required_space = required_space
        self.available_space = available_space


class NetworkError(BlastDockError):
    """Base class for network-related errors"""
    pass


class ServiceUnavailableError(NetworkError):
    """Raised when a required service is unavailable"""
    
    def __init__(self, service: str, endpoint: str):
        super().__init__(f"Service '{service}' is unavailable at {endpoint}")
        self.service = service
        self.endpoint = endpoint


# Error severity levels
class ErrorSeverity:
    """Error severity levels for categorizing exceptions"""
    CRITICAL = "critical"  # Application cannot continue
    ERROR = "error"       # Operation failed but app can continue
    WARNING = "warning"   # Potential issue, operation may continue
    INFO = "info"         # Informational message


# Mapping exceptions to severity levels
EXCEPTION_SEVERITY_MAP = {
    BlastDockError: ErrorSeverity.ERROR,
    ConfigurationError: ErrorSeverity.ERROR,
    TemplateNotFoundError: ErrorSeverity.ERROR,
    TemplateValidationError: ErrorSeverity.ERROR,
    TemplateRenderError: ErrorSeverity.ERROR,
    ProjectNotFoundError: ErrorSeverity.ERROR,
    ProjectAlreadyExistsError: ErrorSeverity.ERROR,
    ProjectConfigurationError: ErrorSeverity.ERROR,
    DeploymentFailedError: ErrorSeverity.ERROR,
    DeploymentNotFoundError: ErrorSeverity.ERROR,
    DockerNotAvailableError: ErrorSeverity.CRITICAL,
    DockerComposeError: ErrorSeverity.ERROR,
    PortValidationError: ErrorSeverity.ERROR,
    PortConflictError: ErrorSeverity.WARNING,
    DomainValidationError: ErrorSeverity.ERROR,
    DatabaseNameValidationError: ErrorSeverity.ERROR,
    PasswordValidationError: ErrorSeverity.ERROR,
    DirectoryNotWritableError: ErrorSeverity.CRITICAL,
    InsufficientSpaceError: ErrorSeverity.CRITICAL,
    ServiceUnavailableError: ErrorSeverity.WARNING,
}


def get_error_severity(exception: Exception) -> str:
    """Get severity level for an exception"""
    return EXCEPTION_SEVERITY_MAP.get(type(exception), ErrorSeverity.ERROR)