"""
Setup configuration for Stockholm.
"""

from setuptools import setup, find_packages
import os


# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "docs", "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Stockholm - Advanced financial sentiment analysis tool"


# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


# Version management
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "src", "__init__.py")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "1.0.0"


setup(
    name="stockholm-finance",
    version=get_version(),
    author="Andrew Farney",
    author_email="contact@andrewfarney.net",
    description="Advanced financial sentiment analysis tool with policy impact assessment",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/aykaym/stockholm",
    project_urls={
        "Bug Tracker": "https://github.com/aykaym/stockholm/issues",
        "Documentation": "https://github.com/aykaym/stockholm/blob/main/docs/README.md",
        "Source Code": "https://github.com/aykaym/stockholm",
    },
    packages=find_packages(include=["src", "src.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0",
            "safety>=2.3.0",
        ],
        "performance": [
            "pytest-benchmark>=4.0.0",
            "memory-profiler>=0.60.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stockholm-finance=src.core.financial_analyzer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["config/*.py"],
    },
    keywords=[
        "finance",
        "sentiment-analysis",
        "nlp",
        "market-analysis",
        "policy-analysis",
        "trading",
        "investment",
        "financial-data",
        "text-analysis",
        "machine-learning",
    ],
    zip_safe=False,
)
