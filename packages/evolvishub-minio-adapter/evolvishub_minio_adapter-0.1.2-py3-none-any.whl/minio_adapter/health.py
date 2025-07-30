"""
Health check utilities for MinIO Adapter.
Provides health check endpoints and monitoring capabilities.
"""

import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .config import MinioConfig
from .client import MinioClient
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class HealthStatus:
    """Health status information."""
    healthy: bool
    status: str
    timestamp: float
    details: Dict[str, Any]
    error: Optional[str] = None


class HealthChecker:
    """Health checker for MinIO adapter."""
    
    def __init__(self, config: MinioConfig):
        """
        Initialize health checker.
        
        Args:
            config: MinIO configuration
        """
        self.config = config
        self.client = None
        self._last_check = None
        self._cache_duration = 30  # Cache health status for 30 seconds
        
    def check_health(self, force: bool = False) -> HealthStatus:
        """
        Check the health of MinIO connection.
        
        Args:
            force: Force a new health check, ignoring cache
            
        Returns:
            HealthStatus object
        """
        current_time = time.time()
        
        # Return cached result if available and not expired
        if (not force and 
            self._last_check and 
            current_time - self._last_check.timestamp < self._cache_duration):
            return self._last_check
        
        try:
            # Initialize client if needed
            if not self.client:
                self.client = MinioClient(self.config)
            
            # Test connection by checking if bucket exists or can be created
            test_bucket = self.config.bucket_name or "health-check-bucket"
            
            # This will test the connection
            bucket_exists = self.client.client.bucket_exists(test_bucket)
            
            details = {
                "endpoint": self.config.endpoint,
                "bucket_name": test_bucket,
                "bucket_exists": bucket_exists,
                "secure": self.config.secure,
                "region": self.config.region
            }
            
            status = HealthStatus(
                healthy=True,
                status="healthy",
                timestamp=current_time,
                details=details
            )
            
            logger.debug("Health check passed", extra={"details": details})
            
        except Exception as e:
            error_msg = str(e)
            details = {
                "endpoint": self.config.endpoint,
                "error": error_msg,
                "error_type": type(e).__name__
            }
            
            status = HealthStatus(
                healthy=False,
                status="unhealthy",
                timestamp=current_time,
                details=details,
                error=error_msg
            )
            
            logger.error("Health check failed", extra={"error": error_msg, "details": details})
        
        self._last_check = status
        return status
    
    def check_readiness(self) -> HealthStatus:
        """
        Check if the service is ready to accept requests.
        
        Returns:
            HealthStatus object
        """
        return self.check_health()
    
    def check_liveness(self) -> HealthStatus:
        """
        Check if the service is alive (basic functionality).
        
        Returns:
            HealthStatus object
        """
        try:
            # Basic liveness check - just verify we can create a client
            if not self.client:
                self.client = MinioClient(self.config)
            
            status = HealthStatus(
                healthy=True,
                status="alive",
                timestamp=time.time(),
                details={"check_type": "liveness"}
            )
            
            logger.debug("Liveness check passed")
            return status
            
        except Exception as e:
            error_msg = str(e)
            status = HealthStatus(
                healthy=False,
                status="dead",
                timestamp=time.time(),
                details={"check_type": "liveness", "error": error_msg},
                error=error_msg
            )
            
            logger.error("Liveness check failed", extra={"error": error_msg})
            return status


def create_health_checker(config_path: str = None, config_type: str = "yaml") -> HealthChecker:
    """
    Create a health checker instance.
    
    Args:
        config_path: Path to configuration file
        config_type: Type of configuration file ('yaml' or 'ini')
        
    Returns:
        HealthChecker instance
    """
    if config_path:
        if config_type == "yaml":
            config = MinioConfig.from_yaml(config_path)
        elif config_type == "ini":
            config = MinioConfig.from_ini(config_path)
        else:
            raise ValueError(f"Unsupported config type: {config_type}")
    else:
        # Create from environment variables
        config = MinioConfig(
            endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
            secure=os.getenv('MINIO_SECURE', 'true').lower() == 'true',
            region=os.getenv('MINIO_REGION'),
            bucket_name=os.getenv('MINIO_BUCKET_NAME')
        )
    
    return HealthChecker(config)
