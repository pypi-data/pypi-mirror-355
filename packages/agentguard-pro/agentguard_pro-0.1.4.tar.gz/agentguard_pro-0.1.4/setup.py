"""
Setup configuration for AgentGuard Python SDK.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentguard-pro",
    version="0.1.4",
    author="AgentGuard Team",
    author_email="support@agentguard.pro",
    description="Python SDK for AgentGuard Pro - AI governance and compliance platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://agentguardpro.com",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "pytest-asyncio>=0.18.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.910",
        ],
    },
    keywords="agentguard ai authorization governance compliance security enterprise",
    license="Proprietary",
)
