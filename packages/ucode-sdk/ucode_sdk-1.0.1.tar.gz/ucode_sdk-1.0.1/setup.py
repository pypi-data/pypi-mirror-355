#!/usr/bin/env python3

"""
Setup script for UCode Python SDK
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    
    # Fallback to manual requirements if file doesn't exist
    if not requirements:
        requirements = [
            'requests>=2.25.0',
            'urllib3>=1.26.0', 
            'paho-mqtt>=1.6.0'
        ]
    
    return requirements

setup(
    name="ucode_sdk",
    version="1.0.0",
    description="UCode Python SDK - A simple and efficient way to interact with the UCode API",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Javohir Udves",
    author_email="support@u-code.io",
    url="https://github.com/ucode-io/ucode-python-sdk",
    packages=find_packages(exclude=['tests*', 'docs*', 'examples*']),
    package_data={
        'ucode_sdk': ['py.typed'],
    },
    include_package_data=True,
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
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Database",
    ],
    keywords="ucode api sdk rest client database crud mongodb postgresql",
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.800',
            'twine>=3.0',
            'wheel>=0.36',
            'build>=0.7.0',
        ],
        'async': [
            'aiohttp>=3.7.0',
        ],
        'test': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'pytest-mock>=3.0',
            'responses>=0.18.0',
        ]
    },
    project_urls={
        "Bug Reports": "https://github.com/ucode-io/ucode-python-sdk/issues",
        "Source": "https://github.com/ucode-io/ucode-python-sdk",
        "Documentation": "https://docs.u-code.io/python-sdk",
    },
    zip_safe=False,
)