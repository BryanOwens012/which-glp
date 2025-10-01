#!/usr/bin/env python3
"""
Setup configuration for reddit-ingestion package
"""

from setuptools import setup, find_packages

setup(
    name="reddit-ingestion",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "praw>=7.7.1",
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
        "APScheduler>=3.10.4",
    ],
)
