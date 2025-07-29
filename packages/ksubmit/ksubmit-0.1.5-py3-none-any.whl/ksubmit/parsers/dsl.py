"""
DSL parser module - parses shell scripts with #$ directives into JobBlock definitions.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional


class JobBlock:
    def __init__(self, name: str = "job", image: str = "ubuntu:latest"):
        self.name = name
        self.image = image
        self.commands: List[str] = []
        self.resources: Dict[str, str] = {}
        self.environment: Dict[str, str] = {}
        self.mounts: Dict[str, str] = {}
        self.mount_overwrite: Dict[str, bool] = {}  # Track which mounts have overwrite enabled
        self.remote_mounts: Dict[str, str] = {}  # Store remote mount information
        self.dependencies: List[str] = []
        self.retries: int = 0
        self.gpus: int = 0
        self.files: List[str] = []
        self.labels: Dict[str, str] = {}
        self.working_dir: Optional[str] = None
        self.entrypoint: Optional[str] = None
        self.stdout: Optional[str] = None
        self.stderr: Optional[str] = None
        self.ttl: Optional[int] = None

    def to_json(self) -> Dict:
        return {
            "name": self.name,
            "image": self.image,
            "commands": self.commands,
            "resources": self.resources,
            "environment": self.environment,
            "mounts": self.mounts,
            "mount_overwrite": self.mount_overwrite,
            "remote_mounts": self.remote_mounts,
            "dependencies": self.dependencies,
            "retries": self.retries,
            "gpus": self.gpus,
            "files": self.files,
            "labels": self.labels,
            "working_dir": self.working_dir,
            "entrypoint": self.entrypoint,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "ttl": self.ttl
        }


def parse_script(script_path: Path, dry_run: bool = False) -> List[JobBlock]:
    if not script_path.exists():
        raise FileNotFoundError(f"Script file not found: {script_path}")

    with open(script_path, 'r') as f:
        lines = f.readlines()

    global_directives = {}
    job_blocks: List[JobBlock] = []
    current_block: Optional[JobBlock] = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#!") or line.startswith("#") and not line.startswith("#$"):
            continue

        if line.startswith("#$"):
            directive = line[2:].strip()

            if directive.startswith("-I "):
                if current_block:
                    job_blocks.append(current_block)
                image = directive[3:].strip()
                current_block = JobBlock(image=image)
                continue

            if current_block:
                parse_directive(current_block, directive)
            else:
                # Store global directives, used if no job block yet
                key = directive.split()[0]
                global_directives.setdefault(key, []).append(directive)
        else:
            if current_block:
                current_block.commands.append(line)

    if current_block:
        job_blocks.append(current_block)

    # Apply global directives to all blocks
    for block in job_blocks:
        for directives in global_directives.values():
            for directive in directives:
                parse_directive(block, directive)

    if dry_run:
        print(json.dumps([job.to_json() for job in job_blocks], indent=2))

    return job_blocks


def parse_directive(job: JobBlock, directive: str):
    if directive.startswith("-N "):
        job.name = directive[3:].strip()
    elif directive.startswith("-l "):
        res_str = directive[3:].strip()
        for res in res_str.split(","):
            if "=" in res:
                k, v = res.split("=", 1)
                job.resources[k.strip()] = v.strip()
    elif directive.startswith("-pe "):
        # Handle parallel environment directive (e.g., -pe smp 4)
        parts = directive[4:].strip().split()
        if len(parts) >= 2 and parts[0] == "smp":
            try:
                cores = int(parts[1])
                job.resources["cpu"] = str(cores)
            except ValueError:
                # Default to 1 core if the value is not a valid integer
                job.resources["cpu"] = "1"
    elif directive.startswith("-v "):
        env_str = directive[3:].strip()
        for pair in env_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                job.environment[k.strip()] = v.strip()
    elif directive.startswith("-mount "):
        mnt = directive[7:].strip()
        if "=" in mnt:
            name_path_part = mnt.split("=", 1)
            name = name_path_part[0].strip()
            path_part = name_path_part[1].strip()

            # Check if --overwrite option is present
            overwrite = False
            if " --overwrite" in path_part:
                overwrite = True
                path = path_part.replace(" --overwrite", "").strip()
            else:
                path = path_part

            job.mounts[name] = path
            job.mount_overwrite[name] = overwrite
    elif directive.startswith("-after "):
        job.dependencies.extend([x.strip() for x in directive[7:].split(",")])
    elif directive.startswith("-retry "):
        try:
            job.retries = int(directive[7:].strip())
        except ValueError:
            job.retries = 0
    elif directive.startswith("-gpus "):
        try:
            job.gpus = int(directive[6:].strip())
        except ValueError:
            job.gpus = 0
    elif directive.startswith("-file "):
        job.files.append(directive[6:].strip())
    elif directive.startswith("-labels "):
        label_str = directive[8:].strip()
        for pair in label_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                job.labels[k.strip()] = v.strip()
    elif directive.startswith("-workdir "):
        job.working_dir = directive[9:].strip()
    elif directive.startswith("-entrypoint "):
        job.entrypoint = directive[12:].strip()
    elif directive.startswith("-o "):
        job.stdout = directive[3:].strip()
    elif directive.startswith("-e "):
        job.stderr = directive[3:].strip()
    elif directive.startswith("-ttl "):
        try:
            job.ttl = int(directive[5:].strip())
        except ValueError:
            # Default to None if the value is not a valid integer
            job.ttl = None
    elif directive.startswith("-remote-mount "):
        mnt = directive[14:].strip()
        if "=" in mnt:
            name_uri_part = mnt.split("=", 1)
            name = name_uri_part[0].strip()
            uri = name_uri_part[1].strip()

            # Store the remote mount information
            job.remote_mounts[name] = uri
