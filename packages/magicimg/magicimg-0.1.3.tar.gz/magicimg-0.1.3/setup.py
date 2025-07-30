#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script cho package magicimg - Fixed version with proper module inclusion
"""

from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

# Lấy phiên bản từ __init__.py
def get_version():
    try:
        with open(os.path.join(here, "magicimg", "__init__.py"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
        return "0.1.3"
    except:
        return "0.1.3"

# Đọc README
def read_readme():
    try:
        with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
            return f.read()
    except:
        return "Advanced image preprocessing package for OCR and computer vision"

# Đọc requirements
def read_requirements():
    try:
        with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except:
        return [
            "opencv-python>=4.5.0",
            "numpy>=1.19.0",
            "matplotlib>=3.3.0",
            "pytesseract>=0.3.8",
            "Pillow>=8.0.0"
        ]

setup(
    name="magicimg",
    version="0.1.3",  # Fixed version - no pyproject.toml conflicts
    author="CoderTeam20266",
    author_email="shumi2011@gmail.com",
    description="Advanced image preprocessing package for OCR and computer vision - Fixed module inclusion",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/CoderTeam20266/MagicImg",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "twine>=3.0"
        ]
    },
    include_package_data=True,
    zip_safe=False,
    keywords="image processing, ocr, preprocessing, computer vision, opencv, tesseract, skew correction, orientation detection",
    entry_points={
        "console_scripts": [
            "magicimg=magicimg.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/CoderTeam20266/MagicImg/issues",
        "Source": "https://github.com/CoderTeam20266/MagicImg/",
        "Documentation": "https://github.com/CoderTeam20266/MagicImg/blob/main/README.md",
        "PyPI": "https://pypi.org/project/magicimg/",
    },
) 