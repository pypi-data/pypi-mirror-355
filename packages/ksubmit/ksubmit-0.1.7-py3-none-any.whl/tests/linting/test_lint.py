"""
Tests for the linting module.
"""
import pytest
import tempfile
import os
from pathlib import Path
from ksubmit.linting.lint import lint_script, LintError, LintErrorCode

def create_temp_script(content):
    """Create a temporary script file with the given content."""
    fd, path = tempfile.mkstemp(suffix=".sh")
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return Path(path)

def test_lint_script_not_found():
    """Test linting a script that doesn't exist."""
    errors = lint_script(Path("nonexistent.sh"))
    assert len(errors) == 1
    assert errors[0].error_code == LintErrorCode.FILE_NOT_FOUND

def test_lint_empty_script():
    """Test linting an empty script."""
    script = create_temp_script("")
    try:
        errors = lint_script(script)
        assert len(errors) == 1
        assert errors[0].error_code == LintErrorCode.NO_JOB_BLOCK
    finally:
        os.unlink(script)

def test_lint_bad_directive_format():
    """Test linting a script with bad directive format."""
    script = create_temp_script("""#!/bin/bash
#$-N my-job
#$ -I ubuntu:latest
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now:
        # 1. Bad directive format
        # 2. Name after image (NAME_AFTER_IMAGE)
        # 3. Missing name (MISSING_NAME)
        assert len(errors) >= 1
        # Check that at least one error is for bad directive format
        assert any(error.error_code == LintErrorCode.BAD_DIRECTIVE_FORMAT for error in errors)
        # Check that the bad directive format error is for line 2
        bad_format_error = next(error for error in errors if error.error_code == LintErrorCode.BAD_DIRECTIVE_FORMAT)
        assert bad_format_error.line_number == 2
    finally:
        os.unlink(script)

def test_lint_unknown_directive():
    """Test linting a script with an unknown directive."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -unknown option
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the unknown directive error
        assert len(errors) >= 1
        # Check that at least one error is for unknown directive
        assert any(error.error_code == LintErrorCode.UNKNOWN_DIRECTIVE for error in errors)
        # Check that the unknown directive error is for line 4
        unknown_directive_error = next(error for error in errors if error.error_code == LintErrorCode.UNKNOWN_DIRECTIVE)
        assert unknown_directive_error.line_number == 4
    finally:
        os.unlink(script)

def test_lint_empty_job_block():
    """Test linting a script with an empty job block."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -I alpine:latest
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the empty job block error
        assert len(errors) >= 1
        # Check that at least one error is for empty job block
        assert any(error.error_code == LintErrorCode.EMPTY_JOB_BLOCK for error in errors)
        # Check that the empty job block error is for line 4
        empty_block_error = next(error for error in errors if error.error_code == LintErrorCode.EMPTY_JOB_BLOCK)
        assert empty_block_error.line_number == 4
    finally:
        os.unlink(script)

def test_lint_duplicate_job_name():
    """Test linting a script with duplicate job names."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
echo "Hello, world!"
#$ -I alpine:latest
#$ -N my-job
echo "Hello again!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the duplicate job name error
        assert len(errors) >= 1
        # Check that at least one error is for duplicate job name
        assert any(error.error_code == LintErrorCode.DUPLICATE_JOB_NAME for error in errors)
        # Check that the duplicate job name error is for line 6
        duplicate_name_error = next(error for error in errors if error.error_code == LintErrorCode.DUPLICATE_JOB_NAME)
        assert duplicate_name_error.line_number == 6
    finally:
        os.unlink(script)

def test_lint_duplicate_env_var():
    """Test linting a script with duplicate environment variables."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -v FOO=bar,FOO=baz
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the duplicate env var error
        assert len(errors) >= 1
        # Check that at least one error is for duplicate env var
        assert any(error.error_code == LintErrorCode.DUPLICATE_ENV_VAR for error in errors)
        # Check that the duplicate env var error is for line 4
        duplicate_env_error = next(error for error in errors if error.error_code == LintErrorCode.DUPLICATE_ENV_VAR)
        assert duplicate_env_error.line_number == 4
    finally:
        os.unlink(script)

def test_lint_invalid_mount_format():
    """Test linting a script with invalid mount format."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -mount invalid_format
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the invalid mount path error
        assert len(errors) >= 1
        # Check that at least one error is for invalid mount path
        assert any(error.error_code == LintErrorCode.MOUNT_PATH_INVALID for error in errors)
        # Check that the invalid mount path error is for line 4
        invalid_mount_error = next(error for error in errors if error.error_code == LintErrorCode.MOUNT_PATH_INVALID)
        assert invalid_mount_error.line_number == 4
        assert invalid_mount_error.rule_id == "MOUNT001"
    finally:
        os.unlink(script)

def test_lint_reserved_mount_name():
    """Test linting a script with a reserved mount name."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -mount users=./data
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # Check that at least one error is for reserved mount name
        assert any(error.error_code == LintErrorCode.MOUNT_RESERVED_NAME for error in errors)
        # Check that the reserved mount name error is for line 4
        reserved_name_error = next(error for error in errors if error.error_code == LintErrorCode.MOUNT_RESERVED_NAME)
        assert reserved_name_error.line_number == 4
        assert reserved_name_error.rule_id == "MOUNT002"
    finally:
        os.unlink(script)

def test_lint_duplicate_mount_name():
    """Test linting a script with duplicate mount names."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -mount data=./data1
#$ -mount data=./data2
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # Check that at least one error is for duplicate mount name
        assert any(error.error_code == LintErrorCode.MOUNT_DUPLICATE_NAME for error in errors)
        # Check that the duplicate mount name error is for line 5
        duplicate_name_error = next(error for error in errors if error.error_code == LintErrorCode.MOUNT_DUPLICATE_NAME)
        assert duplicate_name_error.line_number == 5
        assert duplicate_name_error.rule_id == "MOUNT003"
    finally:
        os.unlink(script)

def test_lint_mount_path_not_found():
    """Test linting a script with a mount path that doesn't exist."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -mount data=./nonexistent_directory
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # Check that at least one error is for mount path not found
        assert any(error.error_code == LintErrorCode.MOUNT_PATH_NOT_FOUND for error in errors)
        # Check that the mount path not found error is for line 4
        path_not_found_error = next(error for error in errors if error.error_code == LintErrorCode.MOUNT_PATH_NOT_FOUND)
        assert path_not_found_error.line_number == 4
        assert path_not_found_error.rule_id == "MOUNT004"
    finally:
        os.unlink(script)

def test_lint_mount_path_mapping_info():
    """Test linting a script with a valid mount path (should show info message)."""
    # Create a temporary directory to mount
    temp_dir = tempfile.mkdtemp()
    try:
        script = create_temp_script(f"""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -mount data={temp_dir}
echo "Hello, world!"
""")
        try:
            errors = lint_script(script)
            # Check that at least one message is for mount path mapping info
            assert any(error.error_code == LintErrorCode.MOUNT_PATH_MAPPING for error in errors)
            # Check that the mount path mapping info is for line 4
            path_mapping_info = next(error for error in errors if error.error_code == LintErrorCode.MOUNT_PATH_MAPPING)
            assert path_mapping_info.line_number == 4
            assert path_mapping_info.rule_id == "MOUNT008"
        finally:
            os.unlink(script)
    finally:
        os.rmdir(temp_dir)

def test_lint_mount_path_escape():
    """Test linting a script with a mount path that attempts to escape."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -mount data=../../../etc
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # Check that at least one error is for mount path escape
        assert any(error.error_code == LintErrorCode.MOUNT_PATH_ESCAPE for error in errors)
        # Check that the mount path escape error is for line 4
        path_escape_error = next(error for error in errors if error.error_code == LintErrorCode.MOUNT_PATH_ESCAPE)
        assert path_escape_error.line_number == 4
        assert path_escape_error.rule_id == "MOUNT010"
    finally:
        os.unlink(script)

def test_lint_remote_mount_invalid_uri():
    """Test linting a script with an invalid remote mount URI."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -remote-mount data=invalid-uri
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # Check that at least one error is for invalid remote mount URI
        assert any(error.error_code == LintErrorCode.REMOTE_MOUNT_INVALID_URI for error in errors)
        # Check that the invalid remote mount URI error is for line 4
        invalid_uri_error = next(error for error in errors if error.error_code == LintErrorCode.REMOTE_MOUNT_INVALID_URI)
        assert invalid_uri_error.line_number == 4
        assert invalid_uri_error.rule_id == "MOUNT005"
    finally:
        os.unlink(script)

def test_lint_remote_mount_shared_bucket():
    """Test linting a script with a remote mount to a shared bucket."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -remote-mount data=gs://shared-bucket/path
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # Check that at least one error is for remote mount to shared bucket
        assert any(error.error_code == LintErrorCode.REMOTE_MOUNT_READONLY_ONLY for error in errors)
        # Check that the remote mount to shared bucket error is for line 4
        shared_bucket_error = next(error for error in errors if error.error_code == LintErrorCode.REMOTE_MOUNT_READONLY_ONLY)
        assert shared_bucket_error.line_number == 4
        assert shared_bucket_error.rule_id == "MOUNT006"
    finally:
        os.unlink(script)

def test_lint_remote_mount_conflict_personal():
    """Test linting a script with a remote mount that conflicts with personal scratch space."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -remote-mount user_data=gs://bucket/path
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # Check that at least one error is for remote mount conflict with personal scratch space
        assert any(error.error_code == LintErrorCode.REMOTE_MOUNT_CONFLICT_PERSONAL for error in errors)
        # Check that the remote mount conflict with personal scratch space error is for line 4
        conflict_error = next(error for error in errors if error.error_code == LintErrorCode.REMOTE_MOUNT_CONFLICT_PERSONAL)
        assert conflict_error.line_number == 4
        assert conflict_error.rule_id == "MOUNT007"
    finally:
        os.unlink(script)

def test_lint_invalid_label_format():
    """Test linting a script with invalid label format."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -labels key1=value1,key2
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the invalid label format error
        assert len(errors) >= 1
        # Check that at least one error is for invalid label format
        assert any(error.error_code == LintErrorCode.INVALID_LABEL_FORMAT for error in errors)
        # Check that the invalid label format error is for line 4
        invalid_label_error = next(error for error in errors if error.error_code == LintErrorCode.INVALID_LABEL_FORMAT)
        assert invalid_label_error.line_number == 4
    finally:
        os.unlink(script)

def test_lint_invalid_resource_value():
    """Test linting a script with invalid resource values."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -l h_vmem=4X
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the invalid resource value error
        assert len(errors) >= 1
        # Check that at least one error is for invalid resource value
        assert any(error.error_code == LintErrorCode.INVALID_RESOURCE_VALUE for error in errors)
        # Check that the invalid resource value error is for line 4
        invalid_resource_error = next(error for error in errors if error.error_code == LintErrorCode.INVALID_RESOURCE_VALUE)
        assert invalid_resource_error.line_number == 4
    finally:
        os.unlink(script)

def test_lint_orphan_directive():
    """Test linting a script with orphan directives."""
    script = create_temp_script("""#!/bin/bash
#$ -l h_vmem=4G
#$ -I ubuntu:latest
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the orphan directive error
        assert len(errors) >= 1
        # Check that at least one error is for orphan directive
        assert any(error.error_code == LintErrorCode.ORPHAN_DIRECTIVE for error in errors)
        # Check that the orphan directive error is for line 2
        orphan_directive_error = next(error for error in errors if error.error_code == LintErrorCode.ORPHAN_DIRECTIVE)
        assert orphan_directive_error.line_number == 2
    finally:
        os.unlink(script)

def test_lint_invalid_retry_count():
    """Test linting a script with invalid retry count."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -retry -1
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the invalid retry count error
        assert len(errors) >= 1
        # Check that at least one error is for invalid retry count
        assert any(error.error_code == LintErrorCode.INVALID_RETRY_COUNT for error in errors)
        # Check that the invalid retry count error is for line 4
        invalid_retry_error = next(error for error in errors if error.error_code == LintErrorCode.INVALID_RETRY_COUNT)
        assert invalid_retry_error.line_number == 4
    finally:
        os.unlink(script)

def test_lint_invalid_gpu_request():
    """Test linting a script with invalid GPU request."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -gpus 0
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        # We expect multiple errors now, including the invalid GPU request error
        assert len(errors) >= 1
        # Check that at least one error is for invalid GPU request
        assert any(error.error_code == LintErrorCode.INVALID_GPU_REQUEST for error in errors)
        # Check that the invalid GPU request error is for line 4
        invalid_gpu_error = next(error for error in errors if error.error_code == LintErrorCode.INVALID_GPU_REQUEST)
        assert invalid_gpu_error.line_number == 4
    finally:
        os.unlink(script)

def test_lint_invalid_dependency():
    """Test linting a script with invalid dependency."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -after nonexistent-job
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        assert len(errors) >= 1
        # Check that at least one error is for invalid dependency
        assert any(error.error_code == LintErrorCode.INVALID_DEPENDENCY for error in errors)
        # Check that the invalid dependency error is for line 3
        invalid_dependency_error = next(error for error in errors if error.error_code == LintErrorCode.INVALID_DEPENDENCY)
        assert invalid_dependency_error.line_number == 3
    finally:
        os.unlink(script)

def test_lint_missing_name():
    """Test linting a script with a missing name directive."""
    script = create_temp_script("""#!/bin/bash
#$ -I ubuntu:latest
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        assert len(errors) == 2  # Should have two errors: NAME_AFTER_IMAGE and MISSING_NAME
        assert any(error.error_code == LintErrorCode.NAME_AFTER_IMAGE for error in errors)
        assert any(error.error_code == LintErrorCode.MISSING_NAME for error in errors)
    finally:
        os.unlink(script)

def test_lint_name_after_image():
    """Test linting a script with a name directive after an image directive."""
    script = create_temp_script("""#!/bin/bash
#$ -I ubuntu:latest
#$ -N my-job
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        assert len(errors) == 1
        assert errors[0].error_code == LintErrorCode.NAME_AFTER_IMAGE
        assert errors[0].line_number == 2
    finally:
        os.unlink(script)

def test_lint_valid_script():
    """Test linting a valid script."""
    script = create_temp_script("""#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -l h_vmem=4G,h_rt=12:00:00
#$ -pe smp 4
#$ -v FOO=bar,BAZ=qux
#$ -retry 2
#$ -labels key1=value1,key2=value2
echo "Hello, world!"
""")
    try:
        errors = lint_script(script)
        if errors:
            print(f"Error: {errors[0]}")
        assert len(errors) == 0
    finally:
        os.unlink(script)
