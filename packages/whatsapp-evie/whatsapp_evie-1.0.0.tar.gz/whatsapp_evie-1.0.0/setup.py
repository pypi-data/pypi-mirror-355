from setuptools import setup, find_packages
import os

# Read version from __init__.py
def get_version():
    with open(os.path.join("whatsapp_evie", "__init__.py"), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

# Development dependencies
dev_requirements = [
    "pytest>=8.0.0,<9.0.0",
    "pytest-asyncio>=0.23.0,<1.0.0",
    "pytest-cov>=4.0.0,<6.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "twine>=4.0.0",
    "build>=0.10.0",
]

setup(
    name="whatsapp-evie",
    version="0.1.0",
    author="Alban Maxhuni, PhD",
    author_email="a.maxhuni@evolvis.ai",
    description="A generic interface to integrate WhatsApp messaging with Evie",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://evolvis.ai",
    project_urls={
        "Bug Reports": "https://github.com/evolvis-ai/whatsapp-evie/issues",
        "Source": "https://github.com/evolvis-ai/whatsapp-evie",
        "Documentation": "https://whatsapp-evie.readthedocs.io/",
    },
    packages=find_packages(exclude=["tests*", "examples*", "docs*"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Typing :: Typed",
    ],
    keywords="whatsapp, messaging, api, webhook, integration, evie, chat, communication",
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "test": [
            "pytest>=8.0.0,<9.0.0",
            "pytest-asyncio>=0.23.0,<1.0.0",
            "pytest-cov>=4.0.0,<6.0.0",
        ],
        "obfuscation": [
            "pyarmor>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "whatsapp-evie=whatsapp_evie.cli:main",
        ],
    },
)