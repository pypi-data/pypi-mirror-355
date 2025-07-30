#!/usr/bin/env python3
"""
Example demonstrating INI configuration usage with the evolvishub-minio-adapter.
This script shows how to load configuration from INI files with different sections.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from minio_adapter import MinioClient, MinioConfig

def demo_ini_config():
    """Demonstrate loading configuration from INI files."""
    print("=== INI Configuration Demo ===")
    
    try:
        # Load default configuration from INI file
        print("1. Loading default configuration from INI file...")
        config_default = MinioConfig.from_ini("../config/minio_config.ini")
        print(f"   Endpoint: {config_default.endpoint}")
        print(f"   Access Key: {config_default.access_key}")
        print(f"   Bucket: {config_default.bucket_name}")
        print(f"   Secure: {config_default.secure}")
        
        # Load production configuration
        print("\n2. Loading production configuration from INI file...")
        config_prod = MinioConfig.from_ini("../config/minio_config.ini", section="minio_production")
        print(f"   Endpoint: {config_prod.endpoint}")
        print(f"   Access Key: {config_prod.access_key}")
        print(f"   Bucket: {config_prod.bucket_name}")
        print(f"   Secure: {config_prod.secure}")
        
        # Load development configuration
        print("\n3. Loading development configuration from INI file...")
        config_dev = MinioConfig.from_ini("../config/minio_config.ini", section="minio_development")
        print(f"   Endpoint: {config_dev.endpoint}")
        print(f"   Access Key: {config_dev.access_key}")
        print(f"   Bucket: {config_dev.bucket_name}")
        print(f"   Secure: {config_dev.secure}")
        
        # Demonstrate environment variable override
        print("\n4. Demonstrating environment variable override...")
        os.environ['MINIO_BUCKET_NAME'] = 'overridden-bucket'
        config_with_env = MinioConfig.from_ini("../config/minio_config.ini")
        print(f"   Original bucket: my-bucket")
        print(f"   Overridden bucket: {config_with_env.bucket_name}")
        
        # Clean up
        del os.environ['MINIO_BUCKET_NAME']
        
        # Create clients with different configurations
        print("\n5. Creating clients with different configurations...")
        
        # Note: These would work with a real MinIO server
        client_default = MinioClient(config_default)
        client_prod = MinioClient(config_prod)
        client_dev = MinioClient(config_dev)
        
        print("   ✓ Default client created")
        print("   ✓ Production client created")
        print("   ✓ Development client created")
        
        print("\n=== Configuration Comparison ===")
        print(f"Default:     {config_default.endpoint} -> {config_default.bucket_name}")
        print(f"Production:  {config_prod.endpoint} -> {config_prod.bucket_name}")
        print(f"Development: {config_dev.endpoint} -> {config_dev.bucket_name}")
        
    except Exception as e:
        print(f"Error: {e}")

def demo_ini_vs_yaml():
    """Compare INI and YAML configuration loading."""
    print("\n=== INI vs YAML Configuration ===")
    
    try:
        # Load from YAML
        config_yaml = MinioConfig.from_yaml("../config/minio_config.yaml")
        print("YAML Configuration:")
        print(f"  Endpoint: {config_yaml.endpoint}")
        print(f"  Bucket: {config_yaml.bucket_name}")
        print(f"  Secure: {config_yaml.secure}")
        
        # Load from INI
        config_ini = MinioConfig.from_ini("../config/minio_config.ini")
        print("\nINI Configuration:")
        print(f"  Endpoint: {config_ini.endpoint}")
        print(f"  Bucket: {config_ini.bucket_name}")
        print(f"  Secure: {config_ini.secure}")
        
        # Compare
        print(f"\nConfigurations match: {config_yaml.to_dict() == config_ini.to_dict()}")
        
    except Exception as e:
        print(f"Error: {e}")

def demo_error_handling():
    """Demonstrate error handling for INI configuration."""
    print("\n=== Error Handling Demo ===")
    
    try:
        # Try to load from non-existent file
        print("1. Testing non-existent file...")
        try:
            MinioConfig.from_ini("non_existent.ini")
        except FileNotFoundError as e:
            print(f"   ✓ Caught expected error: {e}")
        
        # Try to load from non-existent section
        print("\n2. Testing non-existent section...")
        try:
            MinioConfig.from_ini("../config/minio_config.ini", section="non_existent")
        except ValueError as e:
            print(f"   ✓ Caught expected error: {e}")
            
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    """Main function to run all demos."""
    print("MinIO Adapter - INI Configuration Examples")
    print("=" * 50)
    
    demo_ini_config()
    demo_ini_vs_yaml()
    demo_error_handling()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nTo use INI configuration in your code:")
    print("  config = MinioConfig.from_ini('path/to/config.ini')")
    print("  config = MinioConfig.from_ini('path/to/config.ini', section='production')")

if __name__ == "__main__":
    main()
