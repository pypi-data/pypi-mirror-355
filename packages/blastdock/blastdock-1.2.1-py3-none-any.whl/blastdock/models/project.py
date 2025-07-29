"""
Project data models and configuration structures
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class ProjectStatus(str, Enum):
    """Project deployment status"""
    CREATED = "created"
    DEPLOYING = "deploying" 
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    REMOVING = "removing"


class TraefikIntegration(BaseModel):
    """Traefik integration configuration"""
    enabled: bool = False
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    ssl_enabled: bool = False
    labels: Dict[str, str] = Field(default_factory=dict)


class ProjectConfig(BaseModel):
    """Project configuration model"""
    name: str = Field(..., description="Project name")
    template: str = Field(..., description="Template used")
    version: str = Field(default="1.0", description="Configuration version")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Service configuration
    services: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    volumes: List[str] = Field(default_factory=list)
    networks: List[str] = Field(default_factory=list)
    
    # Traefik configuration
    traefik: Optional[TraefikIntegration] = None
    
    # Port configuration
    ports: Dict[str, int] = Field(default_factory=dict)
    
    # Custom configuration
    custom_config: Dict[str, Any] = Field(default_factory=dict)

    @validator('name')
    def validate_name(cls, v):
        """Validate project name format"""
        import re
        from ..constants import PROJECT_NAME_PATTERN
        if not re.match(PROJECT_NAME_PATTERN, v):
            raise ValueError("Project name must contain only alphanumeric characters, hyphens, and underscores")
        return v

    class Config:
        use_enum_values = True


class Project(BaseModel):
    """Complete project model"""
    config: ProjectConfig
    status: ProjectStatus = ProjectStatus.CREATED
    path: str = Field(..., description="Project directory path")
    
    # Runtime information
    containers: List[Dict[str, Any]] = Field(default_factory=list)
    networks: List[str] = Field(default_factory=list)
    volumes: List[str] = Field(default_factory=list)
    
    # Health information
    health_status: Optional[str] = None
    last_deployed: Optional[datetime] = None
    deployment_logs: List[str] = Field(default_factory=list)
    
    # Traefik information
    domains: List[str] = Field(default_factory=list)
    ssl_certificates: List[str] = Field(default_factory=list)

    def is_running(self) -> bool:
        """Check if project is currently running"""
        return self.status == ProjectStatus.RUNNING

    def has_traefik(self) -> bool:
        """Check if project uses Traefik integration"""
        return self.config.traefik is not None and self.config.traefik.enabled

    def get_primary_domain(self) -> Optional[str]:
        """Get the primary domain for this project"""
        if self.domains:
            return self.domains[0]
        if self.has_traefik() and self.config.traefik:
            if self.config.traefik.domain:
                return self.config.traefik.domain
            elif self.config.traefik.subdomain:
                from ..constants import DEFAULT_DOMAIN
                return f"{self.config.traefik.subdomain}.{DEFAULT_DOMAIN}"
        return None

    def get_access_url(self) -> Optional[str]:
        """Get the primary access URL for this project"""
        domain = self.get_primary_domain()
        if domain:
            protocol = "https" if self.has_traefik() and self.config.traefik.ssl_enabled else "http"
            return f"{protocol}://{domain}"
        return None

    class Config:
        use_enum_values = True