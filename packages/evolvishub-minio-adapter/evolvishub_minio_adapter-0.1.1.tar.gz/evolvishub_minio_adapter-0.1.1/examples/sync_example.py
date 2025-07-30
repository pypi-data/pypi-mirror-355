from minio_adapter import MinioClient, MinioConfig

def main():
    # Load configuration
    config = MinioConfig.from_yaml("../config/minio_config.yaml")
    
    # Initialize client
    client = MinioClient(config)
    
    # Ensure bucket exists
    client.ensure_bucket_exists()
    
    # Upload a file
    client.upload_file(
        file_path="example_data.txt",
        object_name="example_data.txt"
    )
    
    # List objects
    objects = client.list_objects()
    print("Objects in bucket:")
    for obj in objects:
        print(f"- {obj['object_name']} ({obj['size']} bytes)")
    
    # Get a presigned URL
    url = client.get_presigned_url("example_data.txt", expires=3600)
    print(f"Presigned URL: {url}")

if __name__ == "__main__":
    main()