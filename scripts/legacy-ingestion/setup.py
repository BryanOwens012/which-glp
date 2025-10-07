#!/usr/bin/env python3
"""
Setup configuration for data-ingestion package
"""

from setuptools import setup, find_packages

setup(
    name="data-ingestion",
    version="0.2.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "praw>=7.7.1",
        "psycopg2-binary>=2.9.9",
        "python-dotenv>=1.0.0",
        "APScheduler>=3.10.4",
        "anthropic>=0.18.0",
        "pydantic>=2.0.0",
    ],
)
