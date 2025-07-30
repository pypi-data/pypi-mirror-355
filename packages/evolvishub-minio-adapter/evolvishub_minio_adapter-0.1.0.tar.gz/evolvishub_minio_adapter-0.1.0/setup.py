from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="evolvishub-minio-adapter",
    version="0.1.0",
    author="Evolvishub",
    author_email="your.email@example.com",
    description="A professional MinIO adapter library with configuration management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/evolvishub-minio-adapter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.7",
    install_requires=[
        "minio>=7.2.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.950",
            "flake8>=4.0.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/evolvishub-minio-adapter/issues",
        "Source": "https://github.com/yourusername/evolvishub-minio-adapter",
    },
)