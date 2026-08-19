"""Setup configuration for NTG."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="news-to-tiktok-generator",
    version="0.1.0",
    author="NTG Team",
    description="Automated news-to-TikTok video generation pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.12",
    install_requires=[
        "sqlalchemy==2.0.23",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "feedparser==6.0.10",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "click==8.1.7",
        "fastapi==0.115.6",
        "uvicorn==0.34.0",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "pytest-cov==4.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ntg=app.cli:cli",
        ]
    },
)
