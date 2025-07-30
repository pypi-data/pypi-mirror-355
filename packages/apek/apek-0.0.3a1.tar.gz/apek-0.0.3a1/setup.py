# -*- coding: utf-8 -*-
"""
This module defines the package's metadata.
"""



from setuptools import setup, find_packages

f1 = open("README.md", "r", encoding="utf-8")

setup(
    name = "apek",
    version = "0.0.3a1",
    author = "Apeking1819",
    description = "A module for creating large numbers.",
    long_description = f1.read(),
    long_description_content_type = "text/markdown",
    packages = find_packages(),
    python_requires = '>=3.12',
    install_requires = [
        "rich >= 14.0.0"
    ]
)

f1.close()
