import pytest
import os
import sys
from pathlib import Path

# Add the project root to the Python path to ensure imports work correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Define fixtures that can be used across all tests

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory as a Path object"""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def ksub_dir():
    """Return the ksubmit directory as a Path object"""
    return Path(__file__).parent.parent / "ksubmit"

@pytest.fixture(scope="session")
def examples_dir():
    """Return the examples directory as a Path object"""
    return Path(__file__).parent.parent / "ksubmit" / "examples"