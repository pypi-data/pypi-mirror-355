"""Setup script for the test-impact-analyzer package."""
from setuptools import setup, find_packages
from typing import List
import os

def read_requirements(filename: str) -> List[str]:
    """Read requirements from file."""
    with open(filename, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

def read_file(filename: str) -> str:
    """Read file contents."""
    with open(filename, "r", encoding="utf-8") as fh:
        return fh.read()

# Read package version from src/version.py if it exists, otherwise use default
version = "0.1.0"
if os.path.exists("src/version.py"):
    with open("src/version.py", "r", encoding="utf-8") as f:
        exec(f.read())
        version = locals().get("__version__", version)

setup(
    name="test-impact-analyzer",
    version=version,
    author="Raj Uppadhyay",
    author_email="uppadhyayraj@gmail.com",
    description="A smart GitHub webhook service that analyzes PRs to determine test impact",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/uppadhyayraj/test-impact-analyzer",
    packages=find_packages(include=['src', 'src.*']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "test-impact-analyzer=src.app:main",
        ],
    },
    package_data={
        "": ["*.md"],
        "src": ["py.typed"],
    },
    include_package_data=True,
)
