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
        "praw>=7.8.2",
        "psycopg2-binary>=2.9.12",
        "python-dotenv>=1.2.2",
        "APScheduler>=3.11.2",
        "openai>=2.41.0",
        "pydantic>=2.13.4",
    ],
)
