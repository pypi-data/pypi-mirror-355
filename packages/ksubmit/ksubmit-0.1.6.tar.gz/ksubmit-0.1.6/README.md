# KSUBMIT - Kubernetes Job Submission Tool with Shorthand Commands

A Python-based CLI tool that parses shell scripts with UGE-like #$ directives and translates them into Kubernetes jobs.

## Overview

KSUBMIT makes it easy to submit batch jobs to Kubernetes clusters using a familiar syntax inspired by Univa Grid Engine (UGE). It allows you to:

- Parse shell scripts with UGE-like #$ directives
- Generate Kubernetes job specifications
- Submit jobs to Kubernetes
- Monitor job status and logs
- Manage job lifecycle

## Installation

```bash
# Install from PyPI
pip install ksubmit

# Or install from source
git clone https://github.com/yourusername/ksubmit.git
cd ksubmit
pip install -e .
```

## Quick Start

1. Initialize KSUBMIT configuration:
```bash
kinit
```

2. Create a job script (example.sh):
```bash
#!/bin/bash
#$ -N my-job
#$ -I ubuntu:latest
#$ -l h_vmem=4G
#$ -l h_rt=01:00:00
#$ -pe smp 2
#$ -mount data=./data
#$ -retry 2
#$ -v ENV_VAR=value

echo "Starting job..."
# Your commands here
echo "Job completed!"
```

3. Submit the job:
```bash
krun example.sh
```

4. Check job status:
```bash
kstat <job-id>
```

5. View job logs:
```bash
klogs <job-id>
```

## Command Reference

| Shorthand Command | Description |
|---------|-------------|
| `kinit` | Initialize user config. Selects Kubernetes cluster context, asks for email, checks namespace exists and is labeled correctly, verifies admin storage transfer pod and shared volume mounts, and saves configuration. |
| `kversion` | Print the current version of KSUB. |
| `kconfig` | View or update stored user config (e.g. `email`, `namespace`, `imagePullSecret`). |
| `krun <file.sh>` | Parse the job script DSL and submit Kubernetes Job(s). Handles mounts, envs, secrets, volumes, retries, etc. |
| `kls` | List submitted jobs in your namespace. Optionally filter by tags or status. |
| `kstat <job-id>` | Get the status of a single job or job block. |
| `klogs <job-id>` | Show logs of a completed or running job. Supports following and output to file. |
| `kdel <job-id>` | Delete a submitted job. |
| `kdesc <job-id>` | Show full details and Kubernetes YAML for a job. |
| `klint <file.sh>` | Lint job scripts for errors. |

## Job Script Directives

KSUB supports the following UGE-like directives in job scripts:

| Directive              | Description                                                            | Example                                  |
| ---------------------- | ---------------------------------------------------------------------- | ---------------------------------------- |
| `-N <name>`            | Job name                                                               | `#$ -N my-job`                           |
| `-I <image>`           | Start a new job block with this container image                        | `#$ -I ubuntu:latest`                    |
| `-l h_vmem=<mem>`      | Memory request → `resources.requests.memory`                           | `#$ -l h_vmem=4G`                        |
| `-l h_rt=<dur>`        | Runtime limit → `activeDeadlineSeconds`                                | `#$ -l h_rt=01:00:00`                    |
| `-pe smp <n>`          | CPUs → `resources.requests.cpu`                                        | `#$ -pe smp 2`                           |
| `-v VAR=val,...`       | Set environment variables                                              | `#$ -v DEBUG=1,LOG_LEVEL=info`           |
| `-mount name=path`     | Mount local path to `/mnt/<name>`                                      | `#$ -mount data=./data`                  |
| `-retry <n>`           | Retry job up to `n` times → `backoffLimit`                             | `#$ -retry 3`                            |
| `-after job-a,...`     | Define job dependencies (wait for other jobs to finish before running) | `#$ -after prepare-data,preprocess`      |
| `-entrypoint <cmd>`    | Override container entrypoint                                          | `#$ -entrypoint bash`                    |
| `-workdir <path>`      | Set working directory inside container                                 | `#$ -workdir /app`                       |
| `-file <path>`         | Copy a file into the container                                         | `#$ -file ./config.yaml`                 |
| `-gpus <n>`            | Request `n` NVIDIA GPUs                                                | `#$ -gpus 1`                             |
| `-labels k=v,...`      | Apply Kubernetes-style labels                                          | `#$ -labels project=ml,env=dev`          |
| `-ttl <seconds>`       | Time to keep Job object in API after it completes → `ttlSecondsAfterFinished` | `#$ -ttl 3600`                           |

## Linting Rules

KSUB validates job scripts against the following rules to ensure they are correctly formatted and semantically valid:

| Rule ID | Category  | Description                                                               | Error Code                   |
| ------- | --------- | ------------------------------------------------------------------------- | ---------------------------- |
| `L001`  | Syntax    | A directive must start with `#$ ` (hash + dollar + space).                | `ERR_BAD_DIRECTIVE_FORMAT`   |
| `L002`  | Syntax    | Unrecognized directive keyword used.                                      | `ERR_UNKNOWN_DIRECTIVE`      |
| `L003`  | Structure | Script must contain at least one `#$ -I <image>` directive.               | `ERR_NO_JOB_BLOCK`           |
| `L004`  | Structure | A job block must start with `#$ -I <image>`.                              | `ERR_MISSING_IMAGE`          |
| `L005`  | Structure | No commands defined for a job block (after `#$ -I`).                      | `ERR_EMPTY_JOB_BLOCK`        |
| `L006`  | Structure | Multiple `#$ -N <name>` directives in one block.                          | `ERR_DUPLICATE_JOB_NAME`     |
| `L007`  | Semantics | Duplicate environment variable defined in `-v` or `-env`.                 | `ERR_DUPLICATE_ENV_VAR`      |
| `L008`  | Semantics | `#$ -mount name=path` must specify a valid local path.                    | `ERR_INVALID_MOUNT_PATH`     |
| `L009`  | Semantics | `#$ -file <path>` must point to a file that exists at submission time.    | `ERR_FILE_NOT_FOUND`         |
| `L010`  | Structure | `#$ -after` references an undefined or invalid job name.                  | `ERR_INVALID_DEPENDENCY`     |
| `L011`  | Structure | Invalid format in `-labels` (must be key=value, comma-separated).         | `ERR_INVALID_LABEL_FORMAT`   |
| `L012`  | Semantics | `#$ -l h_vmem` or `h_rt` has invalid format (e.g., `4X` or `99 hours`).   | `ERR_INVALID_RESOURCE_VALUE` |
| `L013`  | Structure | Directive appears outside of any job block (i.e., before the first `-I`). | `ERR_ORPHAN_DIRECTIVE`       |
| `L014`  | Semantics | `#$ -retry` must be an integer ≥ 0.                                       | `ERR_INVALID_RETRY_COUNT`    |
| `L015`  | Semantics | `#$ -gpus` must be an integer ≥ 1.                                        | `ERR_INVALID_GPU_REQUEST`    |

## Configuration

KSUBMIT stores configuration in `~/.ksubmit/config.yaml`. You can view or update this configuration using:

```bash
# View configuration
kconfig list

# Update configuration
kconfig set namespace my-namespace
kconfig set email me@example.com
```

## Examples

### Simple Example Script

Here's a simple example of a job script that runs a Python container and prints a message:

```bash
#!/bin/bash
#$ -N hello-world
#$ -I docker.io/library/python:3.10
#$ -l h_vmem=2G
#$ -l h_rt=00:10:00
#$ -pe smp 1
#$ -v MSG="Hello from ksubmit"

echo "$MSG"
```

This script:
- Names the job "hello-world"
- Uses the Python 3.10 container image
- Requests 2GB of memory
- Sets a runtime limit of 10 minutes
- Requests 1 CPU
- Sets an environment variable MSG
- Runs a simple echo command to print the environment variable

### Multi-Job Workflow Example

Here's a more complex example that demonstrates a workflow with multiple job blocks and dependencies:

```bash
#!/bin/bash
#$ -N global-setup
#$ -v REFGENOME=hg38
#$ -mount data=./data
#$ -mount code=./pipeline

#$ -I docker.io/continuumio/miniconda3
#$ -N preprocess
#$ -l h_vmem=16G
#$ -l h_rt=04:00:00
#$ -pe smp 4
#$ -file ./pipeline/env.yaml
#$ -entrypoint bash
conda env create -f /mnt/code/env.yaml || true
conda activate pepatac
python /mnt/code/run.py --genome $REFGENOME --input /mnt/data/sample.tsv

#$ -I docker.io/biocontainers/samtools:v1.9-4-deb_cv1
#$ -N analyze
#$ -after preprocess
#$ -l h_vmem=8G
samtools view -b /mnt/data/sample.bam > /mnt/data/sample.filtered.bam
```

This script:
- Sets up global directives that apply to all job blocks
- Creates two job blocks with different container images
- Establishes a dependency where the second job waits for the first to complete
- Mounts local directories into the container
- Copies a file into the container
- Uses environment variables across job blocks

### Basic Job Submission

```bash
krun my-script.sh
```

### Following Job Logs

```bash
klogs <job-id> --follow
# or
klogs <job-id> --output-file logs.txt
```

### Deleting a Job

```bash
kdel <job-id>
```

## Testing

The project uses pytest for testing. Tests are organized in a structure that mirrors the KSUB package structure.

### Running Tests

To install test dependencies:

```bash
pip install -e ".[dev]"
```

To run all tests:

```bash
python -m pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
