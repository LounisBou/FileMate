#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setup script for YoutubeTrailerScraper."""
from pathlib import Path
import importlib.util

from setuptools import setup, find_packages  # pylint: disable=import-error

# Load the _about.py module from src layout
spec = importlib.util.spec_from_file_location(
    "_about", Path(__file__).parent / "src" / "filemate" / "_about.py"
)
about_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(about_module)
about = {
    "__package_name__": about_module.__package_name__,
    "__version__": about_module.__version__,
    "__author__": about_module.__author__,
    "__email__": about_module.__email__,
    "__license__": about_module.__license__,
    "__description__": about_module.__description__,
    "__url__": about_module.__url__,
}

readme = Path("README.md")
long_description = readme.read_text(encoding="utf-8") if readme.exists() else about["__description__"] # pylint: disable=line-too-long

setup(
    name=about["__package_name__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    license=about["__license__"],
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=about["__url__"],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        
        "License :: OSI Approved :: Apache Software License",
        
    ],
    keywords="python template package",
    python_requires=">=3.9",
    install_requires=[
        'diskcache',
        'psutil',
        'redis',
        'setuptools',
        'termcolor',
    ],
    entry_points={
        'console_scripts': [
            'filemate=filemate.__main__:main',  # Command-line entry point
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    extras_require={
        "dev": [
            # Test / Dev tools
            "pytest",
            "pytest-cov",
            "mypy",
            "black",
            "isort",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
