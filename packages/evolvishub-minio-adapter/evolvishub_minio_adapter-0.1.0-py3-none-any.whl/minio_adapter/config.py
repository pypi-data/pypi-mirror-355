import os
import yaml
import configparser
import logging
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class MinioConfig:
    """Configuration class for MinIO client."""
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool = True
    region: Optional[str] = None
    bucket_name: Optional[str] = None

    @classmethod
    def from_yaml(cls, config_path: str) -> 'MinioConfig':
        """Load configuration from a YAML file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Support environment variable overrides
        config_data['endpoint'] = os.getenv('MINIO_ENDPOINT', config_data.get('endpoint'))
        config_data['access_key'] = os.getenv('MINIO_ACCESS_KEY', config_data.get('access_key'))
        config_data['secret_key'] = os.getenv('MINIO_SECRET_KEY', config_data.get('secret_key'))
        config_data['secure'] = os.getenv('MINIO_SECURE', str(config_data.get('secure', True))).lower() == 'true'
        config_data['region'] = os.getenv('MINIO_REGION', config_data.get('region'))
        config_data['bucket_name'] = os.getenv('MINIO_BUCKET_NAME', config_data.get('bucket_name'))

        return cls(**config_data)

    @classmethod
    def from_ini(cls, config_path: str, section: str = 'minio') -> 'MinioConfig':
        """Load configuration from an INI file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        config = configparser.ConfigParser()
        config.read(config_path)

        if section not in config:
            raise ValueError(f"Section '{section}' not found in INI file")

        ini_section = config[section]

        # Extract configuration with type conversion
        config_data = {
            'endpoint': ini_section.get('endpoint'),
            'access_key': ini_section.get('access_key'),
            'secret_key': ini_section.get('secret_key'),
            'secure': ini_section.getboolean('secure', True),
            'region': ini_section.get('region'),
            'bucket_name': ini_section.get('bucket_name')
        }

        # Support environment variable overrides
        config_data['endpoint'] = os.getenv('MINIO_ENDPOINT', config_data.get('endpoint'))
        config_data['access_key'] = os.getenv('MINIO_ACCESS_KEY', config_data.get('access_key'))
        config_data['secret_key'] = os.getenv('MINIO_SECRET_KEY', config_data.get('secret_key'))
        config_data['secure'] = os.getenv('MINIO_SECURE', str(config_data.get('secure', True))).lower() == 'true'
        config_data['region'] = os.getenv('MINIO_REGION', config_data.get('region'))
        config_data['bucket_name'] = os.getenv('MINIO_BUCKET_NAME', config_data.get('bucket_name'))

        # Validate required fields
        if not config_data['endpoint']:
            raise ValueError("endpoint is required")
        if not config_data['access_key']:
            raise ValueError("access_key is required")
        if not config_data['secret_key']:
            raise ValueError("secret_key is required")

        return cls(**config_data)

    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            'endpoint': self.endpoint,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'secure': self.secure,
            'region': self.region,
            'bucket_name': self.bucket_name
        } 