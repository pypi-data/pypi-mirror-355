"""
Kubernetes job generation and management module for ksubmit.
"""
import yaml
import uuid
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from rich.console import Console

from ksubmit.parsers.dsl import JobBlock
from ksubmit.config.user_config import get_namespace, get_email, get_image_pull_secret, get_username
from ksubmit.utils.storage import copy_to_storage_transfer_pod

console = Console()


def generate_job_name(original_name: str) -> Tuple[str, str, str]:
    """
    Generate a job name with UUID according to the requirements:
    - User-given name + last 5 UUID (using 6 for better uniqueness)
    - Total length max of 16 chars
    - 6 UUID characters are mandatory
    - If no name is provided, use full 16 chars UUID
    - User-provided name becomes a label and is slugified

    Args:
        original_name: The original name provided by the user

    Returns:
        Tuple containing (job_name, slugified_name, uid)
    """
    # Slugify the user-provided name
    slugified_name = original_name.lower().replace(" ", "-")

    # Generate a UUID (use only the last 6 characters)
    uid = str(uuid.uuid4())[-6:]

    # If no name provided (or default "job"), use full 16 chars of UUID without hyphens
    if original_name == "job":
        # Use a UUID without hyphens, truncated to 16 chars
        job_name = str(uuid.uuid4()).replace('-', '')[:16]
    else:
        # Store the original slugified name for return
        original_slugified = slugified_name

        # Calculate how much space we have for the name
        # Total length must be 16 chars max
        # 16 - 6 (uid) - 1 (hyphen) = 9 chars max for the name
        max_name_length = 9
        if len(slugified_name) > max_name_length:
            # Only truncate for the job_name, not for the returned slugified_name
            truncated_name = slugified_name[:max_name_length]
            # Combine truncated name with UUID
            job_name = f"{truncated_name}-{uid}"
        else:
            # Combine name with UUID
            job_name = f"{slugified_name}-{uid}"

        # Return the original slugified name, not the truncated one
        return job_name, original_slugified, uid

    return job_name, slugified_name, uid


def sanitize_label_value(value: str) -> str:
    """
    Sanitize a label value to conform to Kubernetes requirements.

    A valid label value must be an empty string or consist of alphanumeric characters,
    '-', '_' or '.', and must start and end with an alphanumeric character.

    Args:
        value: The label value to sanitize

    Returns:
        A sanitized label value that conforms to Kubernetes requirements
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', value)

    # Ensure it starts and ends with an alphanumeric character
    if sanitized and not sanitized[0].isalnum():
        sanitized = 'a' + sanitized
    if sanitized and not sanitized[-1].isalnum():
        sanitized = sanitized + 'z'

    # Handle empty string case
    if not sanitized:
        sanitized = 'empty'

    return sanitized


def generate_job_specs(job_blocks: List[JobBlock], dry_run: bool = False, overwrite: bool = False) -> Tuple[Dict[str, str], bool]:
    """
    Generate Kubernetes job YAML specs from job blocks.

    Args:
        job_blocks: List of JobBlock objects
        dry_run: If True, only output what would be done without actually copying files
        overwrite: If True, overwrite existing directories in destination

    Returns:
        Tuple containing:
        - Dict mapping job names to YAML specs
        - Boolean indicating if there were any mount errors
    """
    job_specs = {}
    mount_errors = False

    for job_block in job_blocks:
        # Generate a unique job name with UUID
        original_name = job_block.name
        job_name, slugified_name, uid = generate_job_name(original_name)

        # Add original name as a label if it's not the default
        if original_name != "job":
            job_block.labels["original-name"] = sanitize_label_value(original_name)

        # Add run_id and job_name as labels for easier identification
        job_block.labels["run_id"] = uid
        job_block.labels["job_name"] = sanitize_label_value(original_name)

        # Handle h_rt (runtime) directive if present
        h_rt_value = None
        active_deadline_seconds = None
        if "h_rt" in job_block.resources:
            h_rt_value = job_block.resources["h_rt"]
            # Remove h_rt from resources as it's not a Kubernetes resource
            del job_block.resources["h_rt"]

            # Convert h_rt to activeDeadlineSeconds
            # Format can be either HH:MM:SS or seconds
            if re.match(r'^\d+:\d+:\d+$', h_rt_value):
                # HH:MM:SS format
                hours, minutes, seconds = map(int, h_rt_value.split(':'))
                active_deadline_seconds = hours * 3600 + minutes * 60 + seconds
            elif re.match(r'^\d+$', h_rt_value):
                # Seconds format
                active_deadline_seconds = int(h_rt_value)
            else:
                console.print(f"[yellow]Warning: Invalid h_rt format: {h_rt_value}. Expected format: 'HH:MM:SS' or seconds. Ignoring.[/yellow]")

        # Get user configuration
        namespace = get_namespace()
        email = get_email()
        image_pull_secret = get_image_pull_secret()

        # Create job spec
        job_spec = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": namespace,
                "labels": {
                    "app": "ksubmit",
                    "owner": sanitize_label_value(email or "unknown")
                }
            },
            "spec": {
                "backoffLimit": job_block.retries,
                # Add activeDeadlineSeconds if h_rt is specified
                **({"activeDeadlineSeconds": active_deadline_seconds} if active_deadline_seconds is not None else {}),
                # Add ttlSecondsAfterFinished if ttl is specified
                **({"ttlSecondsAfterFinished": job_block.ttl} if job_block.ttl is not None else {}),
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "ksubmit",
                            "job-name": job_name
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "main",
                                "image": job_block.image,
                                # Handle entrypoint and commands based on user configuration
                                **_configure_command_and_args(job_block),
                                "resources": _convert_resources(job_block.resources),
                                "env": _convert_environment(job_block.environment)
                            }
                        ],
                        "restartPolicy": "Never"
                    }
                }
            }
        }

        # Add volume mounts if specified
        if job_block.mounts:
            volumes = []
            volume_mounts = []

            for mount_name, mount_path in job_block.mounts.items():
                # Special handling for code mounts
                if mount_name == "code":
                    # Get username for organizing files
                    username = get_username()

                    # Copy files to storage transfer pod
                    # Use mount-specific overwrite flag if available, otherwise use global overwrite flag
                    mount_overwrite = job_block.mount_overwrite.get("code", False) or overwrite
                    success, error_message = copy_to_storage_transfer_pod(
                        source_dir=mount_path,
                        username=username,
                        code_dir_name="code",
                        namespace=namespace,
                        dry_run=dry_run,
                        overwrite=mount_overwrite
                    )

                    if not success:
                        console.print(f"[bold red]Error:[/bold red] Failed to copy code files: {error_message}")
                        mount_errors = True
                        continue

                    # Add a volume mount to the shared storage location
                    volume_name = "scratch-space-code"
                    target_path = f"/mnt/cloud/scratch/{namespace}/code"

                    # Check if we already have this volume
                    if not any(v.get("name") == volume_name for v in volumes):
                        volumes.append({
                            "name": volume_name,
                            "persistentVolumeClaim": {
                                "claimName": "ksubmit-scratch-cloud-pvc",
                                "readOnly": False
                            }
                        })

                    volume_mounts.append({
                        "name": volume_name,
                        "mountPath": target_path,
                        "subPath": f"{namespace}/code",
                        "readOnly": False
                    })

                    # Add environment variable to let the job know where the code is mounted
                    if "env" not in job_spec["spec"]["template"]["spec"]["containers"][0]:
                        job_spec["spec"]["template"]["spec"]["containers"][0]["env"] = []

                    job_spec["spec"]["template"]["spec"]["containers"][0]["env"].append({
                        "name": "KSUB_CODE_DIR",
                        "value": target_path
                    })

                    continue

                # Regular mount handling for other mounts - use shared storage instead of hostPath
                # Get username for organizing files
                username = get_username()

                # Source path and target path
                source = mount_path
                target = f"/mnt/{mount_name}"

                # Check if source path exists and is a directory
                source_path = Path(source)
                if not source_path.exists():
                    console.print(f"[yellow]Warning: Mount source path '{source}' does not exist. Skipping this mount.[/yellow]")
                    continue
                elif not source_path.is_dir():
                    console.print(f"[bold red]Error: Mount source path '{source}' is not a directory. Only directories can be mounted.[/bold red]")
                    console.print(f"[yellow]Skipping mount '{mount_name}={source}'[/yellow]")
                    continue

                # Copy files to storage transfer pod
                # Use mount-specific overwrite flag if available, otherwise use global overwrite flag
                mount_overwrite = job_block.mount_overwrite.get(mount_name, False) or overwrite
                success, error_message = copy_to_storage_transfer_pod(
                    source_dir=source,
                    username=username,
                    code_dir_name=mount_name,
                    namespace=namespace,
                    dry_run=dry_run,
                    overwrite=mount_overwrite
                )

                if not success:
                    console.print(f"[bold red]Error:[/bold red] Failed to copy files for mount '{mount_name}': {error_message}")
                    console.print(f"[yellow]Skipping mount '{mount_name}={source}'[/yellow]")
                    mount_errors = True
                    continue

                # Add a volume mount to the shared storage location
                volume_name = f"scratch-space-{mount_name}"

                # Check if we already have this volume
                if not any(v.get("name") == volume_name for v in volumes):
                    volumes.append({
                        "name": volume_name,
                        "persistentVolumeClaim": {
                            "claimName": "ksubmit-scratch-cloud-pvc",
                            "readOnly": False
                        }
                    })

                volume_mounts.append({
                    "name": volume_name,
                    "mountPath": f"/mnt/cloud/scratch/{namespace}/{mount_name}",
                    "subPath": f"{namespace}/{mount_name}",
                    "readOnly": False
                })

            # Add to job spec
            job_spec["spec"]["template"]["spec"]["volumes"] = volumes
            job_spec["spec"]["template"]["spec"]["containers"][0]["volumeMounts"] = volume_mounts

        # Handle remote mounts if specified
        if job_block.remote_mounts:
            # If we don't already have volumes and volume_mounts lists, create them
            if 'volumes' not in job_spec["spec"]["template"]["spec"]:
                job_spec["spec"]["template"]["spec"]["volumes"] = []
            if 'volumeMounts' not in job_spec["spec"]["template"]["spec"]["containers"][0]:
                job_spec["spec"]["template"]["spec"]["containers"][0]["volumeMounts"] = []

            volumes = job_spec["spec"]["template"]["spec"]["volumes"]
            volume_mounts = job_spec["spec"]["template"]["spec"]["containers"][0]["volumeMounts"]

            for mount_name, gcs_uri in job_block.remote_mounts.items():
                # Extract bucket name and path from GCS URI
                # Format: gs://bucket-name/path
                if gcs_uri.startswith("gs://"):
                    parts = gcs_uri[5:].split("/", 1)
                    bucket_name = parts[0]
                    bucket_path = parts[1] if len(parts) > 1 else ""

                    # Create a unique name for the PV and PVC
                    pv_name = f"ksubmit-remote-{namespace}-{mount_name}"
                    pvc_name = f"ksubmit-remote-{mount_name}-pvc"

                    # Create PV for the GCS bucket
                    pv = {
                        "apiVersion": "v1",
                        "kind": "PersistentVolume",
                        "metadata": {
                            "name": pv_name,
                            "labels": {
                                "ksubmit/role": "remote-mount",
                                "ksubmit/user": namespace
                            }
                        },
                        "spec": {
                            "capacity": {
                                "storage": "1Ti"  # Arbitrary size for cloud storage
                            },
                            "accessModes": ["ReadWriteMany"],
                            "persistentVolumeReclaimPolicy": "Retain",
                            "storageClassName": "",
                            "csi": {
                                "driver": "gcsfuse.csi.storage.gke.io",
                                "volumeHandle": f"{bucket_name}/{bucket_path}",
                                "readOnly": False
                            },
                            "mountOptions": [
                                "implicit-dirs",
                                "uid=1000",
                                "gid=1000"
                            ]
                        }
                    }

                    # Create PVC in user's namespace
                    pvc = {
                        "apiVersion": "v1",
                        "kind": "PersistentVolumeClaim",
                        "metadata": {
                            "name": pvc_name,
                            "namespace": namespace,
                            "labels": {
                                "ksubmit/role": "remote-mount"
                            }
                        },
                        "spec": {
                            "accessModes": ["ReadWriteMany"],
                            "storageClassName": "",
                            "resources": {
                                "requests": {
                                    "storage": "1Ti"  # Match PV size
                                }
                            },
                            "volumeName": pv_name
                        }
                    }

                    # Add volume to job spec
                    volumes.append({
                        "name": f"remote-{mount_name}",
                        "persistentVolumeClaim": {
                            "claimName": pvc_name,
                            "readOnly": False
                        }
                    })

                    # Add volume mount to container
                    volume_mounts.append({
                        "name": f"remote-{mount_name}",
                        "mountPath": f"/mnt/cloud/{mount_name}",
                        "readOnly": False
                    })

                    # Create the PV and PVC resources
                    try:
                        from kubernetes import client
                        from kubernetes.client.rest import ApiException

                        core_api = client.CoreV1Api()

                        # Check if PV already exists
                        pv_exists = False
                        existing_pv = None
                        try:
                            existing_pv = core_api.read_persistent_volume(name=pv_name)
                            pv_exists = True
                            console.print(f"[bold blue]Info:[/bold blue] PersistentVolume [bold]{pv_name}[/bold] already exists")

                            # Check if the existing PV has the same configuration
                            existing_volume_handle = existing_pv.spec.csi.volume_handle if existing_pv.spec.csi else None
                            expected_volume_handle = f"{bucket_name}/{bucket_path}"

                            if existing_volume_handle != expected_volume_handle:
                                console.print(f"[yellow]Warning: Existing PV has different volume handle:[/yellow]")
                                console.print(f"  Existing: {existing_volume_handle}")
                                console.print(f"  Expected: {expected_volume_handle}")
                                console.print(f"[yellow]Using the existing PV. The mount may not work as expected if it points to a different bucket.[/yellow]")
                        except ApiException as e:
                            if e.status == 404:
                                # PV doesn't exist, create it
                                console.print(f"[green]Creating new PersistentVolume [bold]{pv_name}[/bold][/green]")
                                core_api.create_persistent_volume(body=pv)
                            else:
                                raise

                        # Check if PVC already exists
                        pvc_exists = False
                        existing_pvc = None
                        try:
                            existing_pvc = core_api.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
                            pvc_exists = True
                            console.print(f"[bold blue]Info:[/bold blue] PersistentVolumeClaim [bold]{pvc_name}[/bold] already exists in namespace [bold]{namespace}[/bold]")

                            # Check if the existing PVC has the same configuration
                            existing_volume_name = existing_pvc.spec.volume_name

                            if existing_volume_name != pv_name:
                                console.print(f"[yellow]Warning: Existing PVC is bound to a different PV:[/yellow]")
                                console.print(f"  Existing: {existing_volume_name}")
                                console.print(f"  Expected: {pv_name}")
                                console.print(f"[yellow]Using the existing PVC. The mount may not work as expected if it points to a different PV.[/yellow]")
                        except ApiException as e:
                            if e.status == 404:
                                # PVC doesn't exist, create it
                                console.print(f"[green]Creating new PersistentVolumeClaim [bold]{pvc_name}[/bold] in namespace [bold]{namespace}[/bold][/green]")
                                core_api.create_namespaced_persistent_volume_claim(
                                    namespace=namespace,
                                    body=pvc
                                )
                            else:
                                raise

                        # If both PV and PVC exist, ask user what they want to do
                        if pv_exists and pvc_exists and not dry_run:
                            console.print(f"[yellow]Both PV and PVC for mount [bold]{mount_name}[/bold] already exist.[/yellow]")

                            # Check if bucket paths match
                            bucket_paths_match = False
                            if existing_volume_handle == f"{bucket_name}/{bucket_path}":
                                bucket_paths_match = True
                                console.print(f"[green]Bucket paths match for existing PV.[/green]")
                            else:
                                console.print(f"[yellow]Bucket paths don't match:[/yellow]")
                                console.print(f"  Existing: {existing_volume_handle}")
                                console.print(f"  Expected: {bucket_name}/{bucket_path}")

                            console.print(f"[yellow]What would you like to do?[/yellow]")
                            console.print(f"  [bold]1[/bold] - Continue with existing resources")
                            console.print(f"  [bold]2[/bold] - Delete existing resources and create new ones")
                            console.print(f"  [bold]3[/bold] - Update existing resources with new configuration")
                            console.print(f"  [bold]4[/bold] - Skip this mount")
                            console.print(f"[yellow]Enter your choice (1-4):[/yellow]")

                            user_input = input().strip()

                            if user_input == '1':
                                console.print(f"[green]Continuing with existing resources for mount [bold]{mount_name}[/bold][/green]")
                            elif user_input == '2':
                                console.print(f"[yellow]Deleting existing resources for mount [bold]{mount_name}[/bold][/yellow]")
                                try:
                                    # Delete PVC first
                                    core_api.delete_namespaced_persistent_volume_claim(
                                        name=pvc_name,
                                        namespace=namespace
                                    )
                                    console.print(f"[green]Deleted PVC [bold]{pvc_name}[/bold][/green]")

                                    # Delete PV
                                    core_api.delete_persistent_volume(name=pv_name)
                                    console.print(f"[green]Deleted PV [bold]{pv_name}[/bold][/green]")

                                    # Create new PV
                                    core_api.create_persistent_volume(body=pv)
                                    console.print(f"[green]Created new PV [bold]{pv_name}[/bold][/green]")

                                    # Create new PVC
                                    core_api.create_namespaced_persistent_volume_claim(
                                        namespace=namespace,
                                        body=pvc
                                    )
                                    console.print(f"[green]Created new PVC [bold]{pvc_name}[/bold][/green]")
                                except Exception as e:
                                    console.print(f"[bold red]Error deleting/recreating resources for mount {mount_name}:[/bold red] {str(e)}")
                                    console.print(f"[yellow]Skipping mount [bold]{mount_name}[/bold][/yellow]")
                                    continue
                            elif user_input == '3':
                                console.print(f"[yellow]Updating existing resources for mount [bold]{mount_name}[/bold][/yellow]")
                                try:
                                    # Update PV with new configuration
                                    existing_pv.spec.csi.volume_handle = f"{bucket_name}/{bucket_path}"
                                    core_api.patch_persistent_volume(
                                        name=pv_name,
                                        body={"spec": {"csi": {"volumeHandle": f"{bucket_name}/{bucket_path}"}}}
                                    )
                                    console.print(f"[green]Updated PV [bold]{pv_name}[/bold] with new bucket path[/green]")
                                except Exception as e:
                                    console.print(f"[bold red]Error updating resources for mount {mount_name}:[/bold red] {str(e)}")
                                    console.print(f"[yellow]Skipping mount [bold]{mount_name}[/bold][/yellow]")
                                    continue
                            else:
                                console.print(f"[yellow]Skipping mount [bold]{mount_name}[/bold][/yellow]")
                                continue

                    except Exception as e:
                        console.print(f"[bold red]Error creating PV/PVC for remote mount {mount_name}:[/bold red] {str(e)}")
                        mount_errors = True
                else:
                    console.print(f"[bold red]Error:[/bold red] Remote mount URI must start with 'gs://'. Got: {gcs_uri}")
                    mount_errors = True

        # Add image pull secret if specified
        if image_pull_secret:
            job_spec["spec"]["template"]["spec"]["imagePullSecrets"] = [
                {"name": image_pull_secret}
            ]

        # Add h_rt value as a label if it was present
        if h_rt_value:
            job_spec["metadata"]["labels"]["h_rt"] = sanitize_label_value(h_rt_value)

        # Add remote mount information to annotations
        if job_block.remote_mounts:
            if "annotations" not in job_spec["metadata"]:
                job_spec["metadata"]["annotations"] = {}

            # Store remote mount information as JSON in annotations
            remote_mounts_info = {}
            for mount_name, gcs_uri in job_block.remote_mounts.items():
                pv_name = f"ksubmit-remote-{namespace}-{mount_name}"
                pvc_name = f"ksubmit-remote-{mount_name}-pvc"
                remote_mounts_info[mount_name] = {
                    "uri": gcs_uri,
                    "pv": pv_name,
                    "pvc": pvc_name,
                    "mount_path": f"/mnt/cloud/{mount_name}"
                }

            import json
            job_spec["metadata"]["annotations"]["remote_mounts"] = json.dumps(remote_mounts_info)

        # Convert to YAML
        job_specs[job_name] = yaml.dump(job_spec, default_flow_style=False)

    return job_specs, mount_errors


def submit_jobs(job_specs: Dict[str, str]) -> Dict[str, Any]:
    """
    Submit jobs to Kubernetes.

    Args:
        job_specs: Dict mapping job names to YAML specs

    Returns:
        Dict containing:
        - 'submitted': Dict mapping job names to job IDs for successfully submitted jobs
        - 'failed': Dict mapping job names to error messages for failed submissions
    """
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    from ksubmit.utils.storage import store_job

    # Load Kubernetes configuration
    try:
        config.load_kube_config()
    except Exception:
        console.print("[yellow]Warning: Could not load kube config, trying in-cluster config[/yellow]")
        try:
            config.load_incluster_config()
        except Exception as e:
            raise RuntimeError(f"Could not configure Kubernetes client: {str(e)}")

    # Create batch API client
    batch_api = client.BatchV1Api()

    # Submit jobs
    submitted_jobs = {}
    failed_jobs = {}
    namespace = get_namespace()
    email = get_email()

    for job_name, job_yaml in job_specs.items():
        try:
            # Convert YAML to dict
            job_dict = yaml.safe_load(job_yaml)

            # Submit job
            response = batch_api.create_namespaced_job(
                namespace=namespace,
                body=job_dict
            )

            # Generate a job ID (using UUID for now, could use response.metadata.uid)
            job_id = str(uuid.uuid4())[:6]
            submitted_jobs[job_name] = job_name

            # Log remote mount information if present
            if 'annotations' in job_dict.get('metadata', {}) and 'remote_mounts' in job_dict['metadata']['annotations']:
                import json
                remote_mounts = json.loads(job_dict['metadata']['annotations']['remote_mounts'])
                for mount_name, mount_info in remote_mounts.items():
                    console.print(f"[green]Remote mount {mount_name} linked to {mount_info['uri']} at {mount_info['mount_path']}[/green]")

            # Store job information in local database for tracking
            try:
                # Extract container spec for image and commands
                container_spec = job_dict["spec"]["template"]["spec"]["containers"][0]
                image = container_spec.get("image", "")

                # Extract commands
                commands = []
                if "command" in container_spec and "args" in container_spec:
                    # If both command and args are present, combine them
                    cmd = container_spec["command"]
                    args = container_spec["args"]
                    if cmd == ["/bin/sh", "-c"] and len(args) == 1:
                        # Shell command with script
                        commands = args[0].split("\n")
                    else:
                        # Regular command with args
                        commands = [" ".join(cmd + args)]
                elif "command" in container_spec:
                    commands = [" ".join(container_spec["command"])]
                elif "args" in container_spec:
                    commands = [" ".join(container_spec["args"])]

                # Extract resources
                resources = {}
                if "resources" in container_spec:
                    res_spec = container_spec["resources"]
                    if "requests" in res_spec:
                        resources.update(res_spec["requests"])
                    if "limits" in res_spec:
                        # Only add limits that aren't in requests
                        for k, v in res_spec["limits"].items():
                            if k not in resources:
                                resources[k] = v

                # Extract mounts
                mounts = []
                if "volumeMounts" in container_spec:
                    for mount in container_spec["volumeMounts"]:
                        mounts.append(f"{mount['name']}:{mount['mountPath']}")

                # Extract retries
                retries = job_dict["spec"].get("backoffLimit", 0)

                # Extract metadata
                metadata = {
                    "labels": job_dict["metadata"].get("labels", {}),
                    "annotations": job_dict["metadata"].get("annotations", {})
                }

                # Store in database
                store_job(
                    job_id=job_name,  # Use job name as ID for consistency
                    name=job_name,
                    namespace=namespace,
                    status="Pending",
                    image=image,
                    commands=commands,
                    resources=resources,
                    mounts=mounts,
                    retries=retries,
                    owner=email or "unknown",
                    metadata=metadata
                )

                console.print(f"[green]Job {job_name} stored in local database[/green]")
            except Exception as storage_error:
                console.print(f"[yellow]Warning: Could not store job {job_name} in local database: {str(storage_error)}[/yellow]")

        except ApiException as e:
            error_message = str(e)
            failed_jobs[job_name] = error_message
            console.print(f"[bold red]Error submitting job {job_name}:[/bold red] {error_message}")

    # Show summary of failed jobs if any
    if failed_jobs:
        console.print(f"[bold red]⚠️ {len(failed_jobs)} job(s) not submitted due to errors.[/bold red]")

    return {
        'submitted': submitted_jobs,
        'failed': failed_jobs
    }


def _convert_resources(resources: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    Convert resource requests from JobBlock format to Kubernetes format.

    Args:
        resources: Dict of resource requests

    Returns:
        Dict in Kubernetes resource format
    """
    k8s_resources = {"requests": {}, "limits": {}}

    # Map common resource names
    resource_mapping = {
        "memory": "memory",
        "mem": "memory",
        "h_vmem": "memory",  # UGE memory directive
        "cpu": "cpu",
        "gpu": "nvidia.com/gpu"
    }

    # Set default resources if not specified
    default_resources = {
        "memory": "1Gi",  # Default memory: 1GB
        "cpu": "1"        # Default CPU: 1 core
    }

    # Add resources from job block
    for key, value in resources.items():
        # Map resource name
        k8s_key = resource_mapping.get(key.lower(), key)

        # Convert memory units from G to Gi for Kubernetes
        if k8s_key == "memory" and value.endswith("G"):
            value = value.replace("G", "Gi")

        # Remove any extra quotes from values
        if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        # Add to both requests and limits for now
        k8s_resources["requests"][k8s_key] = value
        k8s_resources["limits"][k8s_key] = value

    # Add default resources if not specified
    for k8s_key, default_value in default_resources.items():
        if k8s_key not in k8s_resources["requests"]:
            k8s_resources["requests"][k8s_key] = default_value
            k8s_resources["limits"][k8s_key] = default_value

    return k8s_resources


def _configure_command_and_args(job_block: JobBlock) -> Dict[str, Any]:
    """
    Configure command and args for the container based on entrypoint and commands.

    Handles three cases:
    1. User does not override entrypoint: Let the container run as-is with only args
    2. User overrides with entrypoint: Use the specified entrypoint with shell-wrapped commands
    3. Shell wrapping fallback: Use /bin/sh -c for multiple commands

    Args:
        job_block: JobBlock containing entrypoint and commands

    Returns:
        Dict with command and args keys for the container spec
    """
    container_spec = {}

    if job_block.entrypoint:
        # Case 2: User overrides with entrypoint
        container_spec["command"] = [job_block.entrypoint]
        container_spec["args"] = ["-c", "\n".join(job_block.commands)]
    elif len(job_block.commands) == 1 and isinstance(job_block.commands[0], str) and " " in job_block.commands[0]:
        # Case 3: Single command with arguments needs shell wrapping
        container_spec["command"] = ["/bin/sh", "-c"]
        container_spec["args"] = ["\n".join(job_block.commands)]
    elif len(job_block.commands) > 1:
        # Case 3: Multiple commands need shell wrapping
        container_spec["command"] = ["/bin/sh", "-c"]
        container_spec["args"] = ["\n".join(job_block.commands)]
    else:
        # Case 1: Single command without arguments, let container run as-is
        # Split the command into command and args if it contains spaces
        if job_block.commands:
            command_parts = job_block.commands[0].split()
            if len(command_parts) > 1:
                container_spec["command"] = [command_parts[0]]
                container_spec["args"] = command_parts[1:]
            else:
                container_spec["args"] = job_block.commands
        else:
            # No commands provided, use empty args
            container_spec["args"] = []

    return container_spec


def _convert_environment(env_vars: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Convert environment variables from JobBlock format to Kubernetes format.

    Args:
        env_vars: Dict of environment variables

    Returns:
        List of env var dicts in Kubernetes format
    """
    k8s_env = []

    for key, value in env_vars.items():
        # Remove any extra quotes from values
        if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        k8s_env.append({
            "name": key,
            "value": value
        })

    return k8s_env
