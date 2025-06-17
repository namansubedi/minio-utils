# MinIO Utils

A Python utility package for easy MinIO operations with progress tracking.

## Installation

You can install the package using pip:

```bash
pip install minio-utils
```

## Usage

### Basic Usage

```python
from minio_utils import MinioClient

# Create client from environment variables
minio = MinioClient.from_env()

# Upload a file
result = minio.upload_file(
    bucket_name="my-bucket",
    object_name="path/to/file.txt",
    file_path="local/file.txt"
)
print(f"Upload speed: {result['speed_mbps']:.2f} MB/s")

# Download a file
result = minio.download_file(
    bucket_name="my-bucket",
    object_name="path/to/file.txt",
    file_path="downloaded_file.txt"
)

# List files
files = minio.list_files("my-bucket", prefix="path/to/")

# Delete a file
minio.delete_file("my-bucket", "path/to/file.txt")
```

### Environment Variables

Create a `.env.local` file with your MinIO credentials:

```
MINIO_ENDPOINT=your_minio_endpoint
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
```

## Features

- File upload with progress tracking
- File download with progress tracking
- File deletion
- File listing
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
