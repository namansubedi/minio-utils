from minio import Minio
import os
from tqdm import tqdm
from dotenv import load_dotenv
import time
from datetime import datetime
import threading
from typing import Optional, Union

class ProgressTracker(threading.Thread):
    def __init__(self, total_size: int, operation: str = "Transferring"):
        super().__init__()
        self._total_size = total_size
        self._total_read = 0
        self._progress = tqdm(total=total_size, unit='B', unit_scale=True, desc=operation)
        
    def update(self, bytes_read: int):
        self._total_read += bytes_read
        self._progress.update(bytes_read)
        
    def set_meta(self, **kwargs):
        """Required method for MinIO progress tracking"""
        pass
        
    def close(self):
        self._progress.close()

class MinioClient:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        """
        Initialize MinIO client
        
        Args:
            endpoint (str): MinIO server endpoint
            access_key (str): MinIO access key
            secret_key (str): MinIO secret key
            secure (bool): Whether to use HTTPS (default: False)
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
    
    @classmethod
    def from_env(cls, env_file: str = '.env.local'):
        """
        Create MinIO client from environment variables
        
        Args:
            env_file (str): Path to .env file (default: '.env.local')
        """
        load_dotenv(env_file)
        
        endpoint = os.getenv('MINIO_ENDPOINT')
        access_key = os.getenv('MINIO_ACCESS_KEY')
        secret_key = os.getenv('MINIO_SECRET_KEY')
        
        if not all([endpoint, access_key, secret_key]):
            raise ValueError("MINIO_ENDPOINT, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY must be set in environment file")
        
        return cls(endpoint, access_key, secret_key)
    
    def ensure_bucket_exists(self, bucket_name: str) -> None:
        """Ensure bucket exists, create if it doesn't"""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            print(f"Created bucket: {bucket_name}")
    
    def upload_file(self, bucket_name: str, object_name: str, file_path: str, 
                   show_progress: bool = True) -> dict:
        """
        Upload a file to MinIO with progress tracking
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name to give the object in MinIO
            file_path (str): Path to the file to upload
            show_progress (bool): Whether to show progress bar (default: True)
            
        Returns:
            dict: Upload result information
        """
        self.ensure_bucket_exists(bucket_name)
        
        file_size = os.path.getsize(file_path)
        start_time = time.time()
        
        if show_progress:
            progress = ProgressTracker(file_size, "Uploading")
            progress.start()
            try:
                result = self.client.fput_object(
                    bucket_name,
                    object_name,
                    file_path,
                    progress=progress
                )
            finally:
                progress.close()
        else:
            result = self.client.fput_object(bucket_name, object_name, file_path)
        
        duration = time.time() - start_time
        speed_mbps = (file_size / (1024*1024)) / duration if duration > 0 else 0
        
        return {
            'object_name': result.object_name,
            'bucket_name': result.bucket_name,
            'etag': result.etag,
            'duration': duration,
            'speed_mbps': speed_mbps,
            'file_size': file_size
        }
    
    def download_file(self, bucket_name: str, object_name: str, file_path: str,
                     show_progress: bool = True) -> dict:
        """
        Download a file from MinIO with progress tracking
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name of the object in MinIO
            file_path (str): Path where to save the downloaded file
            show_progress (bool): Whether to show progress bar (default: True)
            
        Returns:
            dict: Download result information
        """
        # Get object info to determine size
        stat = self.client.stat_object(bucket_name, object_name)
        file_size = stat.size
        start_time = time.time()
        
        if show_progress:
            progress = ProgressTracker(file_size, "Downloading")
            progress.start()
            try:
                self.client.fget_object(
                    bucket_name,
                    object_name,
                    file_path,
                    progress=progress
                )
            finally:
                progress.close()
        else:
            self.client.fget_object(bucket_name, object_name, file_path)
        
        duration = time.time() - start_time
        speed_mbps = (file_size / (1024*1024)) / duration if duration > 0 else 0
        
        return {
            'object_name': object_name,
            'bucket_name': bucket_name,
            'file_path': file_path,
            'duration': duration,
            'speed_mbps': speed_mbps,
            'file_size': file_size
        }
    
    def delete_file(self, bucket_name: str, object_name: str) -> None:
        """
        Delete a file from MinIO
        
        Args:
            bucket_name (str): Name of the bucket
            object_name (str): Name of the object to delete
        """
        self.client.remove_object(bucket_name, object_name)
    
    def list_files(self, bucket_name: str, prefix: str = "") -> list:
        """
        List files in a bucket with optional prefix
        
        Args:
            bucket_name (str): Name of the bucket
            prefix (str): Optional prefix to filter objects
            
        Returns:
            list: List of objects in the bucket
        """
        objects = self.client.list_objects(bucket_name, prefix=prefix)
        return [obj.object_name for obj in objects]