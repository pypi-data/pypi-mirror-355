#!/usr/bin/env python3
"""
Depx - 本地多语言依赖统一管理器
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="depx",
    version="0.4.0",
    author="Depx Team",
    author_email="",
    description="本地多语言依赖统一管理器",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/depx",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "depx=depx.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
