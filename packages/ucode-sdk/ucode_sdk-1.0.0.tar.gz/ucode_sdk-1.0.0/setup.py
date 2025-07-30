# setup.py
from setuptools import setup, find_packages
import os

# Read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="ucode-sdk",
    version="1.0.0",
    author="UDevs Team",
    author_email="abdusamatovjavohir@gmail.com",
    description="Official Python SDK for UCode API - CRUD operations for items/objects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Javohir-A/ucode_sdk_python",  # Update with your actual repo
    project_urls={
        "Bug Tracker": "https://github.com/Javohir-A/ucode_sdk_python/issues",
        "Documentation": "https://docs.u-code.io",
        "Source Code": "https://github.com/Javohir-A/ucode_sdk_python",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Database",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "typing-extensions>=4.0.0; python_version<'3.10'",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.10.0",
            "black>=21.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
            "pre-commit>=2.10.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.0",
        ],
    },
    keywords="ucode api sdk crud database mongodb postgresql",
    include_package_data=True,
    zip_safe=False,
)



