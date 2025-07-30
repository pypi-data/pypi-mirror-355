#!/usr/bin/env python
"""
setup.py for mcpstore
"""
from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="mcpstore",
        package_dir={"": "src"},
        packages=find_packages(where="src"),
        include_package_data=True,
        install_requires=[
            "fastapi",
            "fastmcp",
            "httpx"
        ],
        author="ooooofish",
        author_email="ooooofish@126.com",
        description="A composable, ready-to-use MCP toolkit for agents and rapid integration.",
        url="https://github.com/whillhill/mcpstore",
        license="MIT",
    ) 
