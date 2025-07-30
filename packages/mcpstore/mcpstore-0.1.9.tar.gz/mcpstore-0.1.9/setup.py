#!/usr/bin/env python
"""
setup.py for mcpstore
"""
from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="mcpstore",
        version="1.0.0",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        install_requires=[
            "uvicorn",
            "typer",
            "fastapi",
            "rich",
            "python-jose[cryptography]",
            "aiohttp",
            "typing_extensions"
        ],
        entry_points={
            "console_scripts": [
                "mcpstore=mcpstore.cli.main:app_cli",
            ],
        },
        python_requires=">=3.8",
        author="Your Name",
        author_email="your.email@example.com",
        description="MCPStore - 多功能服务管理平台",
        long_description=open("README.md", encoding="utf-8").read(),
        long_description_content_type="text/markdown",
        url="https://github.com/yourusername/mcpstore",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
        ],
    ) 
