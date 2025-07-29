#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for molactivity package
"""

from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Molecular activity prediction using transformer neural networks"


setup(
    name="molactivity",
    version="1.0.5",
    author="Dr. Jiang at BTBU",
    author_email="yale2011@163.com",
    description="Molecular activity prediction using transformer neural networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NATSCREEN/molactivity",
    packages=['molactivity'],

    include_package_data=True,
    package_data={
        '': ['*.csv', '*.dict', '*.md', '*.txt'],
    },
    
    # 不需要外部依赖 - 100% pure Python
    install_requires=[],
    
    entry_points={
        'console_scripts': [
            'mol-train=train:training',
            'mol-predict=predict:main',
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    
    python_requires=">=3.8",
    
    project_urls={
        "Source": "https://github.com/NATSCREEN/molactivity",
    },
    
    license="MIT",
    
    keywords="molecular-activity, machine-learning, transformer, neural-networks, natural-products, drug-discovery",
    
    zip_safe=False,
) 