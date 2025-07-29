from setuptools import setup, find_packages
import os

# Read the contents of the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ksubmit",
    version="0.1.5",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer[all]",  # CLI with colors
        "pyyaml",  # YAML generation
        "kubernetes",  # Kubernetes Python SDK
        "python-dotenv",  # .env file support
        "rich",  # Rich text and formatting in terminal
        "duckdb",  # Optional local database for job tracking
    ],
    extras_require={
        "dev": [
            "pytest",  # Testing framework
            "pytest-cov",  # Coverage reporting
        ],
    },
    entry_points={
        "console_scripts": [
            "krun=ksubmit.cli.shorthand:main",
            "kstat=ksubmit.cli.shorthand:main",
            "klogs=ksubmit.cli.shorthand:main",
            "kdesc=ksubmit.cli.shorthand:main",
            "kdel=ksubmit.cli.shorthand:main",
            "kls=ksubmit.cli.shorthand:main",
            "klist=ksubmit.cli.shorthand:main",
            "klint=ksubmit.cli.shorthand:main",
            "kconfig=ksubmit.cli.shorthand:main",
            "kversion=ksubmit.cli.shorthand:main",
            "kinit=ksubmit.cli.shorthand:main",
        ],
    },
    python_requires=">=3.8",
    author="John Kitonyo",
    author_email="johnkitonyo@outlook.com",
    description="A Kubernetes job submission tool for batch processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="kubernetes, batch, jobs, cli, hpc, grid-engine, uge, job-scheduler",
    url="https://github.com/obistack/ksubmit",
    project_urls={
        "Documentation": "https://github.com/obistack/ksubmit",
        "Source": "https://github.com/obistack/ksubmit",
        "Bug Tracker": "https://github.com/obistack/ksubmit/issues",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Clustering",
        "Topic :: System :: Distributed Computing",
        "Topic :: Scientific/Engineering",
        "Operating System :: OS Independent",
    ],
    # Using SPDX license identifier as recommended by setuptools
    license="MIT",
)
