from minio import Minio
import os
from tqdm import tqdm
from dotenv import load_dotenv
import time
from datetime import datetime
import threading
from typing import Optional, Union, List, Dict, Any, Tuple
import collections
import mimetypes

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
        # Initialize mimetypes
        mimetypes.init()
    
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
    
    def _get_file_type(self, filename: str) -> str:
        """
        Get file type
        
        Args:
            filename: Name of the file
            
        Returns:
            str: File type
        """
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            return "file"
        
        # Map common MIME types to readable names
        mime_types = {
            'image/': 'image',
            'video/': 'video',
            'audio/': 'audio',
            'text/': 'text',
            'application/pdf': 'pdf',
            'application/zip': 'archive',
            'application/json': 'json',
            'application/xml': 'xml',
            'application/javascript': 'javascript',
            'application/x-python': 'python',
        }
        
        for prefix, type_name in mime_types.items():
            if mime_type.startswith(prefix):
                return type_name
        return "file"
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format size in bytes to human readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _format_date(self, date: datetime) -> str:
        """
        Format date to readable string
        
        Args:
            date: Datetime object
            
        Returns:
            str: Formatted date string
        """
        return date.strftime("%Y-%m-%d %H:%M")
    
    def _build_tree(self, objects: list) -> tuple:
        """
        Build a tree structure from a list of objects (robust, no defaultdicts)

        Args:
            objects: List of MinIO objects

        Returns:
            Tuple containing:
            - Dict: Tree structure
            - Dict: Folder statistics (total size and file count)
        """
        tree = {"files": [], "subfolders": {}}
        stats = {"": {"size": 0, "count": 0}}  # root stats

        for obj in objects:
            parts = [p for p in obj.object_name.split('/') if p]
            current = tree
            path_parts = []

            # Traverse/create subfolders
            for part in parts[:-1]:
                path_parts.append(part)
                path_str = '/'.join(path_parts)
                if part not in current["subfolders"]:
                    current["subfolders"][part] = {"files": [], "subfolders": {}}
                current = current["subfolders"][part]
                # Update stats for this folder
                if path_str not in stats:
                    stats[path_str] = {"size": 0, "count": 0}
                stats[path_str]["size"] += obj.size
                stats[path_str]["count"] += 1

            # Handle the file itself (the last part)
            if parts:
                file_name = parts[-1]
                current["files"].append({
                    "name": file_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "type": self._get_file_type(file_name)
                })
                if path_parts:
                    # Add to last folder's stats
                    stats['/'.join(path_parts)]["size"] += 0  # already added above
                    stats['/'.join(path_parts)]["count"] += 0
                else:
                    # File at root
                    stats[""]["size"] += obj.size
                    stats[""]["count"] += 1
        return tree, stats

    def _print_tree(self, tree: dict, stats: dict, prefix: str = "", is_last: bool = True, current_path: str = "") -> None:
        """
        Print the tree structure (robust, no defaultdicts)
        """
        subfolders = list(tree["subfolders"].items())
        for i, (name, content) in enumerate(subfolders):
            is_last_item = i == len(subfolders) - 1
            marker = "└── " if is_last_item else "├── "
            new_path = f"{current_path}/{name}" if current_path else name
            folder_stats = stats.get(new_path, {"size": 0, "count": 0})
            folder_size = self._format_size(folder_stats["size"])
            file_count = folder_stats["count"]
            print(f"{prefix}{marker}[DIR] {name}/")
            print(f"{prefix}{'    ' if is_last_item else '│   '}    Size: {folder_size} | Files: {file_count}")
            # Print files in this folder
            for j, file in enumerate(content["files"]):
                is_last_file = j == len(content["files"]) - 1 and not content["subfolders"]
                file_marker = "└── " if is_last_file else "├── "
                file_size = self._format_size(file["size"])
                mod_date = self._format_date(file["last_modified"])
                print(f"{prefix}{'    ' if is_last_item else '│   '}{file_marker}[{file['type'].upper()}] {file['name']}")
                print(f"{prefix}{'    ' if is_last_item else '│   '}    Size: {file_size} | Modified: {mod_date}")
            # Print subfolders recursively
            new_prefix = prefix + ("    " if is_last_item else "│   ")
            self._print_tree(content, stats, new_prefix, is_last_item, new_path)
        # Print files at the current (root) level
        if not current_path:
            for j, file in enumerate(tree["files"]):
                is_last_file = j == len(tree["files"]) - 1 and not tree["subfolders"]
                file_marker = "└── " if is_last_file else "├── "
                file_size = self._format_size(file["size"])
                mod_date = self._format_date(file["last_modified"])
                print(f"{prefix}{file_marker}[{file['type'].upper()}] {file['name']}")
                print(f"{prefix}    Size: {file_size} | Modified: {mod_date}")

    def list_bucket_structure(self, bucket_name: str, prefix: str = "") -> None:
        """
        Display a tree-like structure of the bucket contents (robust, safe)
        """
        if not self.client.bucket_exists(bucket_name):
            print(f"Bucket '{bucket_name}' does not exist")
            return
        objects = list(self.client.list_objects(bucket_name, prefix=prefix, recursive=True))
        if not objects:
            print(f"Bucket '{bucket_name}' is empty")
            return
        print(f"\nStructure of bucket '{bucket_name}':")
        print("─" * 80)
        tree, stats = self._build_tree(objects)
        self._print_tree(tree, stats)
        print("─" * 80)
        # Print total bucket statistics
        total_size = sum(obj.size for obj in objects)
        total_files = len(objects)
        print(f"\nBucket Statistics:")
        print(f"Total Size: {self._format_size(total_size)}")
        print(f"Total Files: {total_files}")
    
    def list_buckets(self) -> List[Dict[str, Union[str, datetime]]]:
        """
        List all buckets in the MinIO server
        
        Returns:
            List[Dict]: List of dictionaries containing bucket information:
                - name (str): Name of the bucket
                - creation_date (datetime): When the bucket was created
        """
        buckets = self.client.list_buckets()
        return [
            {
                'name': bucket.name,
                'creation_date': bucket.creation_date
            }
            for bucket in buckets
        ]
    
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