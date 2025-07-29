import pytest
import re
from ksub.kubernetes.job import generate_job_name

def test_default_job_name():
    """Test job name generation with default 'job' name"""
    job_name, slugified, uid = generate_job_name("job")

    # For default name, should use full 16-char UUID
    assert len(job_name) == 16, f"Default job name length should be 16, got {len(job_name)}"
    assert slugified == "job"

    # Should be a valid UUID format (hexadecimal)
    assert re.match(r'^[0-9a-f]{16}$', job_name), f"Job name should be a 16-char hex UUID, got {job_name}"

def test_normal_job_name():
    """Test job name generation with a normal name"""
    job_name, slugified, uid = generate_job_name("hello-world")

    # Should follow the format: name-uuid
    assert job_name.startswith("hello-wor"), "Job name should start with truncated original name"
    assert job_name.endswith(uid), f"Job name should end with UUID {uid}"
    assert len(job_name) <= 16, f"Job name should be max 16 chars, got {len(job_name)}"
    assert slugified == "hello-world"

def test_long_job_name():
    """Test job name generation with a long name that exceeds the limit"""
    job_name, slugified, uid = generate_job_name("very-long-name-that-exceeds-limit")

    # Name should be truncated to 9 chars
    assert len(job_name) == 16, f"Long job name should be truncated to 16 chars, got {len(job_name)}"
    assert job_name.startswith("very-long"), "Job name should start with truncated original name"
    assert job_name.endswith(uid), f"Job name should end with UUID {uid}"
    assert slugified == "very-long-name-that-exceeds-limit"

def test_name_with_spaces():
    """Test job name generation with spaces in the name"""
    job_name, slugified, uid = generate_job_name("Name With Spaces")

    # Spaces should be replaced with hyphens
    assert "name-with-" in job_name, "Spaces should be replaced with hyphens"
    assert job_name.endswith(uid), f"Job name should end with UUID {uid}"
    assert len(job_name) <= 16, f"Job name should be max 16 chars, got {len(job_name)}"
    assert slugified == "name-with-spaces"
