import asyncio
from typing import Optional, BinaryIO, Union, List, Dict, Any
from minio import Minio
from minio.error import S3Error
from concurrent.futures import ThreadPoolExecutor
from .config import MinioConfig


class AsyncMinioClient:
    """Asynchronous wrapper for MinIO client operations."""

    def __init__(self, config: MinioConfig, max_workers: int = 10):
        """Initialize the async MinIO client with configuration."""
        self.config = config
        self.client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
            region=config.region
        )
        self.bucket_name = config.bucket_name
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def ensure_bucket_exists(self, bucket_name: Optional[str] = None) -> None:
        """Ensure the specified bucket exists, create if it doesn't."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")
        
        exists = await self._run_in_executor(self.client.bucket_exists, bucket)
        if not exists:
            await self._run_in_executor(self.client.make_bucket, bucket)

    # Helper method to run blocking operations in executor
    async def _run_in_executor(self, func, *args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, 
            lambda: func(*args, **kwargs)
        )

    async def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload a file to MinIO asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        await self.ensure_bucket_exists(bucket)

        if not object_name:
            object_name = file_path.split('/')[-1]

        try:
            await self._run_in_executor(
                self.client.fput_object,
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata
            )
            return object_name
        except S3Error as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    async def download_file(
        self,
        object_name: str,
        file_path: str,
        bucket_name: Optional[str] = None
    ) -> None:
        """Download a file from MinIO asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            await self._run_in_executor(
                self.client.fget_object,
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path
            )
        except S3Error as e:
            raise Exception(f"Failed to download file: {str(e)}")

    async def upload_data(
        self,
        data: Union[bytes, BinaryIO],
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload data to MinIO asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        await self.ensure_bucket_exists(bucket)

        try:
            await self._run_in_executor(
                self.client.put_object,
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

    async def get_object(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> bytes:
        """Get object data from MinIO asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            response = await self._run_in_executor(
                self.client.get_object,
                bucket_name=bucket,
                object_name=object_name
            )
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to get object: {str(e)}")

    async def list_objects(
        self,
        prefix: str = "",
        recursive: bool = True,
        bucket_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List objects in a bucket asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            objects = await self._run_in_executor(
                self.client.list_objects,
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

    async def remove_object(
        self,
        object_name: str,
        bucket_name: Optional[str] = None
    ) -> None:
        """Remove an object from MinIO asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            await self._run_in_executor(
                self.client.remove_object,
                bucket_name=bucket,
                object_name=object_name
            )
        except S3Error as e:
            raise Exception(f"Failed to remove object: {str(e)}")

    async def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600,
        bucket_name: Optional[str] = None,
        method: str = "GET"
    ) -> str:
        """Generate a presigned URL for an object asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            return await self._run_in_executor(
                self.client.presigned_url,
                method=method,
                bucket_name=bucket,
                object_name=object_name,
                expires=expires
            )
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    async def get_bucket_policy(
        self,
        bucket_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get bucket policy asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            return await self._run_in_executor(
                self.client.get_bucket_policy,
                bucket
            )
        except S3Error as e:
            raise Exception(f"Failed to get bucket policy: {str(e)}")

    async def set_bucket_policy(
        self,
        policy: Dict[str, Any],
        bucket_name: Optional[str] = None
    ) -> None:
        """Set bucket policy asynchronously."""
        bucket = bucket_name or self.bucket_name
        if not bucket:
            raise ValueError("No bucket name specified")

        try:
            await self._run_in_executor(
                self.client.set_bucket_policy,
                bucket,
                policy
            )
        except S3Error as e:
            raise Exception(f"Failed to set bucket policy: {str(e)}")

    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)