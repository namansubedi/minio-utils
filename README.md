# MinIO Utils

A Python utility package for easy MinIO operations with progress tracking.

## Installation

You can install the package using pip:

```bash
pip install git+https://github.com/namansubedi/minio-utils.git
```

## Environment Variables

Create a `.env.local` file with your MinIO credentials:

```
MINIO_ENDPOINT=your_minio_endpoint
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
```

## API Documentation

### MinioClient

The main class for interacting with MinIO.

#### Initialization

```python
from minio_utils import MinioClient

# Method 1: Direct initialization
minio = MinioClient(
    endpoint="your_minio_endpoint",
    access_key="your_access_key",
    secret_key="your_secret_key",
    secure=False  # Set to True for HTTPS
)

# Method 2: From environment variables
minio = MinioClient.from_env(env_file=".env.local")  # env_file is optional
```

### Methods

#### list_buckets()

Lists all buckets in the MinIO server.

**Returns:**

```python
List[Dict[str, Union[str, datetime]]]
# Example:
[
    {
        'name': 'bucket1',
        'creation_date': datetime(2024, 3, 15, 14, 30)
    },
    {
        'name': 'bucket2',
        'creation_date': datetime(2024, 3, 15, 15, 45)
    }
]
```

#### list_bucket_structure(bucket_name: str, prefix: str = "")

Displays a tree-like structure of the bucket contents.

**Parameters:**

- `bucket_name` (str): Name of the bucket to list
- `prefix` (str, optional): Filter objects by prefix

**Output:**

```
Structure of bucket 'my-bucket':
├── [DIR] folder1/
│       Size: 4.50 MB | Files: 3
│   ├── [PYTHON] file1.py
│   │       Size: 1.25 MB | Modified: 2024-03-15 14:30
...
```

#### upload_file(bucket_name: str, object_name: str, file_path: str, show_progress: bool = True)

Uploads a file to MinIO with progress tracking.

**Parameters:**

- `bucket_name` (str): Name of the bucket
- `object_name` (str): Name to give the object in MinIO
- `file_path` (str): Path to the file to upload
- `show_progress` (bool, optional): Whether to show progress bar (default: True)

**Returns:**

```python
Dict[str, Any]
# Example:
{
    'object_name': 'path/to/file.txt',
    'bucket_name': 'my-bucket',
    'etag': 'etag123',
    'duration': 1.5,
    'speed_mbps': 2.5,
    'file_size': 1024
}
```

#### download_file(bucket_name: str, object_name: str, file_path: str, show_progress: bool = True)

Downloads a file from MinIO with progress tracking.

**Parameters:**

- `bucket_name` (str): Name of the bucket
- `object_name` (str): Name of the object in MinIO
- `file_path` (str): Path where to save the downloaded file
- `show_progress` (bool, optional): Whether to show progress bar (default: True)

**Returns:**

```python
Dict[str, Any]
# Example:
{
    'object_name': 'path/to/file.txt',
    'bucket_name': 'my-bucket',
    'file_path': 'downloaded_file.txt',
    'duration': 1.5,
    'speed_mbps': 2.5,
    'file_size': 1024
}
```

#### delete_file(bucket_name: str, object_name: str)

Deletes a file from MinIO.

**Parameters:**

- `bucket_name` (str): Name of the bucket
- `object_name` (str): Name of the object to delete

#### list_files(bucket_name: str, prefix: str = "")

Lists files in a bucket with optional prefix.

**Parameters:**

- `bucket_name` (str): Name of the bucket
- `prefix` (str, optional): Filter objects by prefix

**Returns:**

```python
List[str]
# Example:
[
    'path/to/file1.txt',
    'path/to/file2.txt'
]
```

#### ensure_bucket_exists(bucket_name: str)

Ensures a bucket exists, creates it if it doesn't.

**Parameters:**

- `bucket_name` (str): Name of the bucket to check/create

## Features

- File upload with progress tracking
- File download with progress tracking
- File deletion
- File listing
- Bucket structure visualization
- Automatic bucket creation
- Speed and duration tracking
- Environment variable configuration

## Requirements

- Python 3.7+
- minio>=7.1.0
- tqdm>=4.65.0
- python-dotenv>=1.0.0

## License

MIT License
