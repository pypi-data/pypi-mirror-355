"""
Linting module for ksub - validates shell scripts with #$ directives.
"""
import re
import os
import posixpath
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any

# Define error codes
class LintErrorCode:
    BAD_DIRECTIVE_FORMAT = "ERR_BAD_DIRECTIVE_FORMAT"
    UNKNOWN_DIRECTIVE = "ERR_UNKNOWN_DIRECTIVE"
    NO_JOB_BLOCK = "ERR_NO_JOB_BLOCK"
    MISSING_IMAGE = "ERR_MISSING_IMAGE"
    EMPTY_JOB_BLOCK = "ERR_EMPTY_JOB_BLOCK"
    DUPLICATE_JOB_NAME = "ERR_DUPLICATE_JOB_NAME"
    DUPLICATE_ENV_VAR = "ERR_DUPLICATE_ENV_VAR"
    INVALID_MOUNT_PATH = "ERR_INVALID_MOUNT_PATH"
    FILE_NOT_FOUND = "ERR_FILE_NOT_FOUND"
    INVALID_DEPENDENCY = "ERR_INVALID_DEPENDENCY"
    INVALID_LABEL_FORMAT = "ERR_INVALID_LABEL_FORMAT"
    INVALID_RESOURCE_VALUE = "ERR_INVALID_RESOURCE_VALUE"
    ORPHAN_DIRECTIVE = "ERR_ORPHAN_DIRECTIVE"
    INVALID_RETRY_COUNT = "ERR_INVALID_RETRY_COUNT"
    INVALID_GPU_REQUEST = "ERR_INVALID_GPU_REQUEST"
    MISSING_NAME = "ERR_MISSING_NAME"
    NAME_AFTER_IMAGE = "ERR_NAME_AFTER_IMAGE"
    JOB_BLOCK_MUST_START_WITH_IMAGE = "ERR_JOB_BLOCK_MUST_START_WITH_IMAGE"
    NAME_MUST_FOLLOW_IMAGE = "ERR_NAME_MUST_FOLLOW_IMAGE"
    NO_DIRECTIVES_BETWEEN_I_AND_N = "ERR_NO_DIRECTIVES_BETWEEN_I_AND_N"

    # Mount-specific error codes
    MOUNT_PATH_INVALID = "ERROR_MOUNT_PATH_INVALID"
    MOUNT_RESERVED_NAME = "ERROR_MOUNT_RESERVED_NAME"
    MOUNT_DUPLICATE_NAME = "ERROR_MOUNT_DUPLICATE_NAME"
    MOUNT_PATH_NOT_FOUND = "ERROR_MOUNT_PATH_NOT_FOUND"
    REMOTE_MOUNT_INVALID_URI = "ERROR_REMOTE_MOUNT_INVALID_URI"
    REMOTE_MOUNT_READONLY_ONLY = "ERROR_REMOTE_MOUNT_READONLY_ONLY"
    REMOTE_MOUNT_CONFLICT_PERSONAL = "ERROR_REMOTE_MOUNT_CONFLICT_PERSONAL"
    MOUNT_PATH_MAPPING = "INFO_MOUNT_PATH_MAPPING"
    MOUNT_WRITABLE_LOCATION = "ERROR_MOUNT_WRITABLE_LOCATION"
    MOUNT_PATH_ESCAPE = "ERROR_MOUNT_PATH_ESCAPE"

# Define valid directives
VALID_DIRECTIVES = {
    "-N": "Job name",
    "-I": "Container image",
    "-l": "Resource request",
    "-pe": "CPU request",
    "-v": "Environment variables",
    "-mount": "Mount local path",
    "-remote-mount": "Mount remote path",
    "-retry": "Retry count",
    "-after": "Job dependencies",
    "-entrypoint": "Container entrypoint",
    "-workdir": "Working directory",
    "-file": "File to copy",
    "-gpus": "GPU request",
    "-labels": "Kubernetes labels",
    "-o": "Standard output file",
    "-e": "Standard error file",
    "-ttl": "Time to live"
}

# Define reserved mount names
RESERVED_MOUNT_NAMES = {"users", "common", "scratch", "tmp", "temp", "data", "shared", "system", "config"}

# Define valid cloud storage URI patterns
VALID_CLOUD_URI_PATTERNS = [
    r'^gs://[a-z0-9][-_.a-z0-9]*[a-z0-9](/[-_.a-z0-9]+)*$',  # Google Cloud Storage
    r'^s3://[a-z0-9][-_.a-z0-9]*[a-z0-9](/[-_.a-z0-9]+)*$',   # AWS S3
    r'^az://[a-z0-9][-_.a-z0-9]*[a-z0-9](/[-_.a-z0-9]+)*$'    # Azure Blob Storage
]

# Define shared bucket patterns (buckets that should be read-only)
SHARED_BUCKET_PATTERNS = [
    r'^gs://shared-.*$',
    r'^gs://public-.*$',
    r'^gs://common-.*$',
    r'^s3://shared-.*$',
    r'^s3://public-.*$',
    r'^s3://common-.*$',
    r'^az://shared-.*$',
    r'^az://public-.*$',
    r'^az://common-.*$'
]

class LintError:
    """Class representing a linting error."""
    def __init__(self, line_number: int, error_code: str, message: str, rule_id: str):
        self.line_number = line_number
        self.error_code = error_code
        self.message = message
        self.rule_id = rule_id

    def __str__(self) -> str:
        return f"Line {self.line_number}: [{self.rule_id}] {self.message} ({self.error_code})"

def lint_script(script_path: Path) -> List[LintError]:
    """
    Lint a shell script with #$ directives.

    Args:
        script_path: Path to the script file

    Returns:
        List of LintError objects
    """
    if not script_path.exists():
        return [LintError(0, LintErrorCode.FILE_NOT_FOUND, f"Script file not found: {script_path}", "L009")]

    with open(script_path, 'r') as f:
        lines = f.readlines()

    errors = []
    job_blocks = []
    current_block = None
    job_names = set()
    env_vars = {}
    in_job_block = False
    has_commands = False
    seen_name_before_image = False  # Track if name directive was seen before image directive
    pending_name = None  # Store the name directive that was seen before the image directive

    # Variables to track the new rules
    expecting_first_directive = True  # Track if we're expecting the first directive in a job block
    last_directive_was_image = False  # Track if the last directive was an image directive
    expecting_name_directive = False  # Track if we're expecting a name directive next

    # Flag to track if we've seen any directives yet
    seen_any_directive = False

    # Track mount names to check for duplicates
    mount_names = set()
    remote_mount_names = set()

    for i, line in enumerate(lines):
        line_number = i + 1
        line = line.strip()

        # Skip empty lines and non-directive comments
        if not line or line.startswith("#!") or (line.startswith("#") and not line.startswith("#$")):
            continue

        # Check for directive format
        if line.startswith("#$"):
            # Check if directive format is correct (hash + dollar + space)
            if not line.startswith("#$ "):
                errors.append(LintError(
                    line_number,
                    LintErrorCode.BAD_DIRECTIVE_FORMAT,
                    "A directive must start with '#$ ' (hash + dollar + space)",
                    "L001"
                ))
                continue

            directive = line[3:].strip()
            directive_key = directive.split()[0] if directive else ""

            # Check if this is the first directive in the script
            if not seen_any_directive:
                seen_any_directive = True
                # Check if the first directive is not an image directive
                if not directive.startswith("-I "):
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.JOB_BLOCK_MUST_START_WITH_IMAGE,
                        "Job block must start with an image directive -I.",
                        "L019"
                    ))
                    expecting_first_directive = False  # No longer expecting the first directive

            # Check for unknown directive
            if directive_key not in VALID_DIRECTIVES:
                errors.append(LintError(
                    line_number,
                    LintErrorCode.UNKNOWN_DIRECTIVE,
                    f"Unknown directive: {directive_key}",
                    "L002"
                ))
                continue

            # Check if we're expecting a name directive but got something else
            if expecting_name_directive and not directive.startswith("-N "):
                errors.append(LintError(
                    line_number,
                    LintErrorCode.NO_DIRECTIVES_BETWEEN_I_AND_N,
                    "No directives allowed between -I and -N.",
                    "L021"
                ))
                expecting_name_directive = False  # Reset the flag

            # Check if this is the first directive in a job block and it's not an image directive
            if in_job_block and expecting_first_directive and not directive.startswith("-I "):
                errors.append(LintError(
                    line_number,
                    LintErrorCode.JOB_BLOCK_MUST_START_WITH_IMAGE,
                    "Job block must start with an image directive -I.",
                    "L019"
                ))
                expecting_first_directive = False  # No longer expecting the first directive

            # Check for new job block
            if directive.startswith("-I "):
                if current_block and not has_commands:
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.EMPTY_JOB_BLOCK,
                        "No commands defined for the previous job block",
                        "L005"
                    ))

                # Reset expecting_first_directive for the next job block
                expecting_first_directive = True

                current_block = {"line": line_number, "name": pending_name, "dependencies": []}
                job_blocks.append(current_block)
                in_job_block = True
                has_commands = False
                seen_name_before_image = False  # Reset for the next block
                pending_name = None  # Reset pending name

                # Set flags for the new rules
                expecting_first_directive = False  # No longer expecting the first directive
                last_directive_was_image = True   # Last directive was an image directive
                expecting_name_directive = True   # Expecting a name directive next
                continue

            # Check for orphan directive (before first -I)
            if not in_job_block and directive_key != "-N":
                errors.append(LintError(
                    line_number,
                    LintErrorCode.ORPHAN_DIRECTIVE,
                    f"Directive appears outside of any job block (before the first -I): {directive}",
                    "L013"
                ))
                continue

            # Process specific directives
            if directive.startswith("-N "):
                name = directive[3:].strip()

                # Check if we're expecting a name directive (should follow image directive)
                if in_job_block and last_directive_was_image:
                    # This is good - name directive follows image directive
                    last_directive_was_image = False
                    expecting_name_directive = False
                elif in_job_block and expecting_name_directive:
                    # Error: There was something between -I and -N
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.NO_DIRECTIVES_BETWEEN_I_AND_N,
                        "No directives allowed between -I and -N.",
                        "L021"
                    ))
                    last_directive_was_image = False
                    expecting_name_directive = False
                elif in_job_block and not expecting_first_directive:
                    # Error: Name directive doesn't immediately follow image directive
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.NAME_MUST_FOLLOW_IMAGE,
                        "Job name directive -N must immediately follow image directive -I.",
                        "L020"
                    ))

                if current_block and current_block["name"]:
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.DUPLICATE_JOB_NAME,
                        f"Multiple -N directives in one block. Previous name: {current_block['name']}",
                        "L006"
                    ))
                elif name in job_names:
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.DUPLICATE_JOB_NAME,
                        f"Duplicate job name: {name}",
                        "L006"
                    ))
                else:
                    job_names.add(name)
                    if current_block:
                        current_block["name"] = name
                    # Set the flag to indicate that a name directive was seen before an image directive
                    if not in_job_block:
                        seen_name_before_image = True
                        pending_name = name

            elif directive.startswith("-v "):
                env_str = directive[3:].strip()
                for pair in env_str.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        k = k.strip()
                        if k in env_vars:
                            errors.append(LintError(
                                line_number,
                                LintErrorCode.DUPLICATE_ENV_VAR,
                                f"Duplicate environment variable: {k}",
                                "L007"
                            ))
                        else:
                            env_vars[k] = v.strip()

            elif directive.startswith("-mount "):
                mnt = directive[7:].strip()
                if "=" in mnt:
                    name_path_part = mnt.split("=", 1)
                    name = name_path_part[0].strip()
                    path_part = name_path_part[1].strip()

                    # Check if --overwrite option is present
                    if " --overwrite" in path_part:
                        path = path_part.replace(" --overwrite", "").strip()
                    else:
                        path = path_part

                    # MOUNT001: Validate that mount paths are valid local directory paths
                    if not path or not os.path.isabs(path) and not path.startswith('./') and not path.startswith('../'):
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_PATH_INVALID,
                            f"Mount path must be a valid relative or absolute local directory path: {path}",
                            "MOUNT001"
                        ))

                    # MOUNT002: Check that mount names don't use reserved names
                    if name.lower() in RESERVED_MOUNT_NAMES:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_RESERVED_NAME,
                            f"Mount name '{name}' is reserved and cannot be used",
                            "MOUNT002"
                        ))

                    # MOUNT003: Ensure no duplicate mount names in the same script
                    if name in mount_names or name in remote_mount_names:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_DUPLICATE_NAME,
                            f"Duplicate mount name: {name}",
                            "MOUNT003"
                        ))
                    else:
                        mount_names.add(name)

                    # MOUNT004: Verify that local paths exist at submission time
                    if not os.path.exists(path):
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_PATH_NOT_FOUND,
                            f"Mount path does not exist: {path}",
                            "MOUNT004"
                        ))
                    elif not os.path.isdir(path):
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_PATH_INVALID,
                            f"Mount path is not a directory: {path}",
                            "MOUNT001"
                        ))

                    # MOUNT008: Provide info about mount path mapping
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.MOUNT_PATH_MAPPING,
                        f"Mount point '{name}' will be mapped to '/mnt/cloud/scratch/<namespace>/{name}/' inside the container",
                        "MOUNT008"
                    ))

                    # MOUNT010: Prevent path escaping
                    if '..' in path.split('/'):
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_PATH_ESCAPE,
                            f"Mount path must not attempt to escape predefined container mount roots: {path}",
                            "MOUNT010"
                        ))
                else:
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.MOUNT_PATH_INVALID,
                        f"Invalid mount format. Expected 'name=path', got: {mnt}",
                        "MOUNT001"
                    ))

            elif directive.startswith("-remote-mount "):
                mnt = directive[13:].strip()
                if "=" in mnt:
                    name, uri = mnt.split("=", 1)
                    name = name.strip()
                    uri = uri.strip()

                    # MOUNT002: Check that mount names don't use reserved names
                    if name.lower() in RESERVED_MOUNT_NAMES:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_RESERVED_NAME,
                            f"Mount name '{name}' is reserved and cannot be used",
                            "MOUNT002"
                        ))

                    # MOUNT003: Ensure no duplicate mount names in the same script
                    if name in mount_names or name in remote_mount_names:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_DUPLICATE_NAME,
                            f"Duplicate mount name: {name}",
                            "MOUNT003"
                        ))
                    else:
                        remote_mount_names.add(name)

                    # MOUNT005: Validate remote mount URIs
                    valid_uri = False
                    for pattern in VALID_CLOUD_URI_PATTERNS:
                        if re.match(pattern, uri):
                            valid_uri = True
                            break

                    if not valid_uri:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.REMOTE_MOUNT_INVALID_URI,
                            f"Remote mount URI is not valid: {uri}",
                            "MOUNT005"
                        ))

                    # MOUNT006: Ensure remote mounts to shared buckets are read-only
                    is_shared_bucket = False
                    for pattern in SHARED_BUCKET_PATTERNS:
                        if re.match(pattern, uri):
                            is_shared_bucket = True
                            break

                    if is_shared_bucket:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.REMOTE_MOUNT_READONLY_ONLY,
                            f"Remote mount to shared bucket must be read-only: {uri}",
                            "MOUNT006"
                        ))

                    # MOUNT007: Check for conflicts between remote mounts and personal scratch space
                    if name.startswith('user_') or name == 'personal':
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.REMOTE_MOUNT_CONFLICT_PERSONAL,
                            f"Remote mount name '{name}' conflicts with personal scratch space naming",
                            "MOUNT007"
                        ))

                    # MOUNT008: Provide info about mount path mapping
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.MOUNT_PATH_MAPPING,
                        f"Remote mount point '{name}' will be mapped to '/mnt/cloud/scratch/<namespace>/{name}/' inside the container",
                        "MOUNT008"
                    ))

                    # MOUNT009: Ensure writable mounts are inside personal scratch space
                    if not uri.startswith('gs://') and not uri.startswith('s3://') and not uri.startswith('az://'):
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.MOUNT_WRITABLE_LOCATION,
                            f"All user writable mounts must be inside their personal scratch space path: {uri}",
                            "MOUNT009"
                        ))
                else:
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.REMOTE_MOUNT_INVALID_URI,
                        f"Invalid remote mount format. Expected 'name=uri', got: {mnt}",
                        "MOUNT005"
                    ))

            elif directive.startswith("-file "):
                file_path = directive[6:].strip()
                if not os.path.exists(file_path):
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.FILE_NOT_FOUND,
                        f"File not found: {file_path}",
                        "L009"
                    ))

            elif directive.startswith("-after "):
                deps = [x.strip() for x in directive[7:].split(",")]
                if current_block:
                    current_block["dependencies"].extend(deps)

            elif directive.startswith("-labels "):
                label_str = directive[8:].strip()
                for pair in label_str.split(","):
                    if "=" not in pair:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.INVALID_LABEL_FORMAT,
                            f"Invalid label format. Expected 'key=value', got: {pair}",
                            "L011"
                        ))

            elif directive.startswith("-l "):
                res_str = directive[3:].strip()
                for res in res_str.split(","):
                    if "=" in res:
                        k, v = res.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        # Check for h_vmem and h_rt format
                        if k == "h_vmem":
                            if not re.match(r'^\d+[KMGT]?$', v):
                                errors.append(LintError(
                                    line_number,
                                    LintErrorCode.INVALID_RESOURCE_VALUE,
                                    f"Invalid memory format for h_vmem: {v}. Expected format: '4G', '1024M', etc.",
                                    "L012"
                                ))
                        elif k == "h_rt":
                            if not re.match(r'^\d+:\d+:\d+$', v) and not re.match(r'^\d+$', v):
                                errors.append(LintError(
                                    line_number,
                                    LintErrorCode.INVALID_RESOURCE_VALUE,
                                    f"Invalid runtime format for h_rt: {v}. Expected format: 'HH:MM:SS' or seconds",
                                    "L012"
                                ))

            elif directive.startswith("-retry "):
                try:
                    retry_count = int(directive[7:].strip())
                    if retry_count < 0:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.INVALID_RETRY_COUNT,
                            f"Retry count must be >= 0, got: {retry_count}",
                            "L014"
                        ))
                except ValueError:
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.INVALID_RETRY_COUNT,
                        f"Invalid retry count: {directive[7:].strip()}. Must be an integer.",
                        "L014"
                    ))

            elif directive.startswith("-gpus "):
                try:
                    gpu_count = int(directive[6:].strip())
                    if gpu_count < 1:
                        errors.append(LintError(
                            line_number,
                            LintErrorCode.INVALID_GPU_REQUEST,
                            f"GPU count must be >= 1, got: {gpu_count}",
                            "L015"
                        ))
                except ValueError:
                    errors.append(LintError(
                        line_number,
                        LintErrorCode.INVALID_GPU_REQUEST,
                        f"Invalid GPU count: {directive[6:].strip()}. Must be an integer.",
                        "L015"
                    ))

        else:
            # This is a command, not a directive
            if in_job_block:
                has_commands = True
                expecting_first_directive = False  # No longer at the beginning of a job block
                expecting_name_directive = False   # No longer expecting a name directive

    # Check for empty job block at the end
    if current_block and not has_commands:
        errors.append(LintError(
            current_block["line"],
            LintErrorCode.EMPTY_JOB_BLOCK,
            "No commands defined for the last job block",
            "L005"
        ))

    # Check for missing job blocks
    if not job_blocks:
        errors.append(LintError(
            0,
            LintErrorCode.NO_JOB_BLOCK,
            "Script must contain at least one '#$ -I <image>' directive",
            "L003"
        ))

    # Check for invalid dependencies
    job_names_list = list(job_names)
    for block in job_blocks:
        # Check if the job block has a name
        if block["name"] is None:
            errors.append(LintError(
                block["line"],
                LintErrorCode.MISSING_NAME,
                "Job block must have a name directive (-N)",
                "L017"
            ))

        for dep in block["dependencies"]:
            if dep not in job_names_list:
                errors.append(LintError(
                    block["line"],
                    LintErrorCode.INVALID_DEPENDENCY,
                    f"Dependency references an undefined job name: {dep}",
                    "L010"
                ))

    return errors
