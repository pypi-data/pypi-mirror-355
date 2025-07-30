from typing import Optional, BinaryIO, Union, List, Dict, Any
from minio import Minio
from minio.error import S3Error
from .config import MinioConfig


class MinioClient:
    """A professional wrapper for MinIO client operations."""

    def __init__(self, config: MinioConfig):
        """Initialize the MinIO client with configuration."""
        self.config = config
        self.client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
            region=config.region
        )
        self.bucket_name = config.bucket_name

    def ensure_bucket_exists(self, bucket_name: Optional[str] = None) -> None:
        """Ensure the specified bucket exists, create if it doesn't."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")
        
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload a file to MinIO."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        self.ensure_bucket_exists(bucket)
        
        if not object_name:
            object_name = file_path.split('/')[-1]

        try:
            self.client.fput_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata
            )
            return object_name
        except S3Error as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    def download_file(
        self,
        object_name: str,
        file_path: str,
        bucket_name: Optional[str] = None
    ) -> None:
        """Download a file from MinIO."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            self.client.fget_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path
            )
        except S3Error as e:
            raise Exception(f"Failed to download file: {str(e)}")

    def upload_data(
        self,
        data: Union[bytes, BinaryIO],
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload data to MinIO."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        self.ensure_bucket_exists(bucket)

        try:
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=data,
                length=-1 if isinstance(data, BinaryIO) else len(data),
                content_type=content_type,
                metadata=metadata
            )
            return object_name
        except S3Error as e:
            raise Exception(f"Failed to upload data: {str(e)}")

    def get_object(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> bytes:
        """Get object data from MinIO."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            response = self.client.get_object(
                bucket_name=bucket,
                object_name=object_name
            )
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to get object: {str(e)}")

    def list_objects(
        self,
        prefix: str = "",
        recursive: bool = True,
        bucket_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List objects in a bucket."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            objects = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix,
                recursive=recursive
            )
            return [{
                'object_name': obj.object_name,
                'size': obj.size,
                'last_modified': obj.last_modified,
                'etag': obj.etag
            } for obj in objects]
        except S3Error as e:
            raise Exception(f"Failed to list objects: {str(e)}")

    def remove_object(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> None:
        """Remove an object from MinIO."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            self.client.remove_object(
                bucket_name=bucket,
                object_name=object_name
            )
        except S3Error as e:
            raise Exception(f"Failed to remove object: {str(e)}")

    def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600,
        bucket_name: Optional[str] = None,
        method: str = "GET"
    ) -> str:
        """Generate a presigned URL for an object."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            return self.client.presigned_url(
                method=method,
                bucket_name=bucket,
                object_name=object_name,
                expires=expires
            )
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    def get_bucket_policy(
        self,
        bucket_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get bucket policy."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            return self.client.get_bucket_policy(bucket)
        except S3Error as e:
            raise Exception(f"Failed to get bucket policy: {str(e)}")

    def set_bucket_policy(
        self,
        policy: Dict[str, Any],
        bucket_name: Optional[str] = None
    ) -> None:
        """Set bucket policy."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            self.client.set_bucket_policy(bucket, policy)
        except S3Error as e:
            raise Exception(f"Failed to set bucket policy: {str(e)}") 