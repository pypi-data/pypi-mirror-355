"""
Identifier utilities for KSUB.

This module provides functions for generating and validating identifiers
used in KSUB, such as job IDs and submission IDs.
"""
import re
import time
import uuid
from typing import Optional

def validate_identifier(identifier: Optional[str], required: bool = True) -> Optional[str]:
    """
    Validate job or submission identifier.

    Args:
        identifier: The identifier to validate
        required: Whether the identifier is required

    Returns:
        The validated identifier

    Raises:
        ValueError: If the identifier is invalid
    """
    if required and not identifier:
        raise ValueError("Job ID or Run ID is required. Use 'kstat <job-id>' or 'kstat <run-id>'.")

    if identifier:
        if identifier.startswith("run-"):
            # Validate submission ID format with run- prefix
            if not re.match(r"run-[a-f0-9]{8,}", identifier):
                raise ValueError(
                    f"Invalid run ID format: {identifier}. Expected format: run-<8+ hex chars>.\n"
                    f"Example: run-64a7b123abcd"
                )
        elif identifier.startswith("sub-"):
            # The 'sub-' prefix is no longer supported
            raise ValueError(
                f"The 'sub-' prefix is no longer supported. Please use 'run-' prefix instead.\n"
                f"Example: run-64a7b123abcd"
            )
        else:
            # Validate job ID format
            if not re.match(r"[a-z0-9-]+", identifier):
                raise ValueError(
                    f"Invalid job ID format: {identifier}. Job IDs must contain only lowercase letters, numbers, and hyphens.\n"
                    f"Example: my-job-123"
                )

    return identifier

def generate_submission_id() -> str:
    """
    Generate a unique, collision-resistant submission ID.

    Returns:
        A unique submission ID
    """
    # Use timestamp + random component for better uniqueness
    timestamp = int(time.time())
    random_component = uuid.uuid4().hex[:4]
    return f"run-{timestamp:x}{random_component}"
