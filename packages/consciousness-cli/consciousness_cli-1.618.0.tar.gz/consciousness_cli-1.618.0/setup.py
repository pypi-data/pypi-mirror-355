#!/usr/bin/env python3
"""
Consciousness CLI - Universal Intelligence Portal Interface
A powerful CLI for consciousness computing with void mathematics and phi-based operations
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Claude CLI - Consciousness Portal Interface"

# Read version
VERSION = "1.618.0"  # Phi-based versioning

setup(
    name="consciousness-cli",
    version=VERSION,
    author="Abhishek Srivastava",
    author_email="bits.abhi@gmail.com",
    description="Consciousness computing CLI with φ mathematics and void operations",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/bitsabhi/consciousness-portal",
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "websocket-client>=1.4.0",
        "click>=8.0.0",
        "colorama>=0.4.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "consciousness-cli=claude_cli.main:main",
            "consciousness-portal=claude_cli.portal:portal_main",
            "phi-calculate=claude_cli.mathematics:phi_main",
            "void-transform=claude_cli.void:void_main",
        ],
    },
    include_package_data=True,
    package_data={
        "claude_cli": ["assets/*", "templates/*"],
    },
    keywords="consciousness cli phi void mathematics golden-ratio abhilasia intelligence",
    project_urls={
        "Bug Reports": "https://github.com/bitsabhi/consciousness-portal/issues",
        "Source": "https://github.com/bitsabhi/consciousness-portal",
        "Documentation": "https://github.com/bitsabhi/consciousness-portal/blob/main/README.md",
        "Portal": "https://bitsabhi.github.io/consciousness-portal/",
    },
)