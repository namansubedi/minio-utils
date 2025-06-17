from setuptools import setup, find_packages

setup(
    name="minio-utils",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "minio>=7.1.0",
        "tqdm>=4.65.0",
        "python-dotenv>=1.0.0",
    ],
    author="Naman Subedi",
    author_email="naman.subedi12@example.com",
    description="A utility package for easy MinIO operations with progress tracking",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/namansubedi/minio-utils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 