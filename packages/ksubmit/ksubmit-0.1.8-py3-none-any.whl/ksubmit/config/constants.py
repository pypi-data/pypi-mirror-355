"""
Constants module for ksubmit - contains centralized configuration paths.
"""
from pathlib import Path

# Configuration paths
CONFIG_DIR = Path.cwd() / ".ksubmit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
SECRETS_FILE = CONFIG_DIR / "secrets.env"
