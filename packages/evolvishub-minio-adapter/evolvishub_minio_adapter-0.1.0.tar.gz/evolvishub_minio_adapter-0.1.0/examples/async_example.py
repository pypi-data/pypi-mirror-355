import asyncio
from minio_adapter import AsyncMinioClient, MinioConfig

async def main():
    # Load configuration
    config = MinioConfig.from_yaml("../config/minio_config.yaml")
    
    # Initialize async client
    client = AsyncMinioClient(config)
    
    # Ensure bucket exists
    await client.ensure_bucket_exists()
    
    # Upload a file asynchronously
    await client.upload_file(
        file_path="example_data.txt",
        object_name="example_data.txt"
    )
    
    # List objects asynchronously
    objects = await client.list_objects()
    print("Objects in bucket:")
    for obj in objects:
        print(f"- {obj['object_name']} ({obj['size']} bytes)")
    
    # Get a presigned URL asynchronously
    url = await client.get_presigned_url("example_data.txt", expires=3600)
    print(f"Presigned URL: {url}")

if __name__ == "__main__":
    asyncio.run(main())