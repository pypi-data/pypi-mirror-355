"""
Kubernetes client wrapper module for ksub.
"""
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from rich.console import Console

from ksub.config.user_config import get_namespace, get_context

console = Console()


def initialize_kubernetes_client(context: Optional[str] = None) -> None:
    """
    Initialize the Kubernetes client.

    Tries to load kube config from default location, falls back to in-cluster config.
    If no context is provided, uses the context from the ksub config file.

    Args:
        context: Optional Kubernetes context to use. If None, uses the context from ksub config.

    Raises:
        RuntimeError: If Kubernetes client cannot be configured
    """
    # If no context is provided, use the one from ksub config
    if context is None:
        context = get_context()
    try:
        config.load_kube_config(context=context)
    except Exception:
        console.print("[yellow]Warning: Could not load kube config, trying in-cluster config[/yellow]")
        try:
            config.load_incluster_config()
        except Exception as e:
            raise RuntimeError(f"Could not configure Kubernetes client: {str(e)}")


def get_job_logs(job_id: str, container: Optional[str] = None,
                 tail: Optional[int] = None, follow: bool = False) -> str:
    """
    Get logs for a job.

    Args:
        job_id: ID of the job
        container: Name of the container to get logs from (default: first container)
        tail: Number of lines to show from the end
        follow: Whether to follow the logs in real-time

    Returns:
        String containing the logs

    Raises:
        RuntimeError: If job or pod cannot be found
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API clients
    core_api = client.CoreV1Api()
    batch_api = client.BatchV1Api()

    namespace = get_namespace()

    # Find the job by ID
    try:
        # For now, we're assuming job_id is the job name
        # In a real implementation, we would look up the job by ID in our local database
        job_name = job_id

        # Get the job
        job = batch_api.read_namespaced_job(name=job_name, namespace=namespace)

        # Find the pod associated with the job
        label_selector = f"job-name={job_name}"
        pods = core_api.list_namespaced_pod(namespace=namespace, label_selector=label_selector)

        if not pods.items:
            raise RuntimeError(f"No pods found for job {job_name}")

        # Get the first pod (or the most recent one if there are multiple)
        pod = pods.items[0]
        pod_name = pod.metadata.name

        # If container is not specified, use the first container
        if not container:
            container = pod.spec.containers[0].name

        # Get logs
        logs = core_api.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail,
            follow=follow
        )

        return logs

    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"Job {job_id} not found in namespace {namespace}")
        else:
            raise RuntimeError(f"Error getting logs: {str(e)}")


def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a job.

    Args:
        job_id: ID of the job

    Returns:
        Dict containing job status information

    Raises:
        RuntimeError: If job cannot be found
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    batch_api = client.BatchV1Api()

    namespace = get_namespace()

    try:
        # For now, we're assuming job_id is the job name
        # In a real implementation, we would look up the job by ID in our local database
        job_name = job_id

        # Get the job
        job = batch_api.read_namespaced_job(name=job_name, namespace=namespace)

        # Extract status information
        status = {
            "name": job.metadata.name,
            "namespace": job.metadata.namespace,
            "created_at": job.metadata.creation_timestamp,
            "active": job.status.active or 0,
            "succeeded": job.status.succeeded or 0,
            "failed": job.status.failed or 0,
            "completion_time": job.status.completion_time,
            "conditions": [],
            "job_id": job.metadata.name,  # Kubernetes job ID
            "start_time": job.status.start_time if hasattr(job.status, 'start_time') else None,
            "labels": job.metadata.labels or {}  # Include labels for identification
        }

        # Calculate duration if possible
        if status["start_time"] and status["completion_time"]:
            start = status["start_time"]
            end = status["completion_time"]
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            if isinstance(end, str):
                end = datetime.fromisoformat(end.replace('Z', '+00:00'))
            duration = end - start
            status["duration"] = str(duration)
        elif status["start_time"]:
            # Job is still running, calculate duration from start to now
            start = status["start_time"]
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            duration = datetime.now().astimezone() - start
            status["duration"] = str(duration)
        else:
            status["duration"] = "N/A"

        # Determine status string
        if job.status.active:
            status["status"] = "Running"
        elif job.status.succeeded:
            status["status"] = "Succeeded"
        elif job.status.failed:
            status["status"] = "Failed"
        else:
            status["status"] = "Unknown"

        # Add conditions if available
        if job.status.conditions:
            for condition in job.status.conditions:
                status["conditions"].append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                    "last_transition_time": condition.last_transition_time
                })

        return status

    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"Job {job_id} not found in namespace {namespace}")
        else:
            raise RuntimeError(f"Error getting job status: {str(e)}")


def delete_job(job_id: str) -> bool:
    """
    Delete a job.

    Args:
        job_id: ID of the job

    Returns:
        True if successful, False otherwise

    Raises:
        RuntimeError: If job cannot be found
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    batch_api = client.BatchV1Api()

    namespace = get_namespace()

    try:
        # For now, we're assuming job_id is the job name
        # In a real implementation, we would look up the job by ID in our local database
        job_name = job_id

        # Delete the job
        batch_api.delete_namespaced_job(
            name=job_name,
            namespace=namespace,
            body=client.V1DeleteOptions(
                propagation_policy="Background"
            )
        )

        return True

    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"Job {job_id} not found in namespace {namespace}")
        else:
            raise RuntimeError(f"Error deleting job: {str(e)}")

    return False


def describe_job(job_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a job, including its YAML representation.

    Args:
        job_id: ID of the job

    Returns:
        Dict containing job details and YAML representation

    Raises:
        RuntimeError: If job cannot be found
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    batch_api = client.BatchV1Api()

    namespace = get_namespace()

    try:
        # For now, we're assuming job_id is the job name
        # In a real implementation, we would look up the job by ID in our local database
        job_name = job_id

        # Get the job
        job = batch_api.read_namespaced_job(name=job_name, namespace=namespace)

        # Get the job status
        status = get_job_status(job_id)

        # Convert job to dict for YAML representation
        import yaml
        job_dict = client.ApiClient().sanitize_for_serialization(job)
        job_yaml = yaml.dump(job_dict, default_flow_style=False)

        # Get pod information for this job
        core_api = client.CoreV1Api()
        pods = core_api.list_namespaced_pod(
            namespace=namespace,
            label_selector=f"job-name={job_name}"
        )

        pod_info = []
        for pod in pods.items:
            pod_info.append({
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "node": pod.spec.node_name if pod.spec.node_name else "Not assigned",
                "ip": pod.status.pod_ip if pod.status.pod_ip else "No IP",
                "start_time": pod.status.start_time,
                "container_statuses": [
                    {
                        "name": container_status.name,
                        "ready": container_status.ready,
                        "restart_count": container_status.restart_count,
                        "state": str(container_status.state)
                    }
                    for container_status in (pod.status.container_statuses or [])
                ]
            })

        # Extract resource information from the job
        image = "N/A"
        cpu_request = "N/A"
        memory_request = "N/A"
        gpu_request = "N/A"

        if job.spec.template and job.spec.template.spec and job.spec.template.spec.containers:
            container = job.spec.template.spec.containers[0]

            # Extract image
            image = container.image if container.image else "N/A"

            # Extract resource requests
            if container.resources and container.resources.requests:
                cpu_request = container.resources.requests.get('cpu', "N/A")
                memory_request = container.resources.requests.get('memory', "N/A")

            # Extract GPU request (usually in limits with key nvidia.com/gpu)
            if container.resources and container.resources.limits:
                gpu_request = container.resources.limits.get('nvidia.com/gpu', "N/A")

        # Combine all information
        description = {
            "job_id": job_id,
            "name": job.metadata.name,
            "namespace": job.metadata.namespace,
            "status": status,
            "pods": pod_info,
            "yaml": job_yaml,
            "image": image,
            "cpu_request": cpu_request,
            "memory_request": memory_request,
            "gpu_request": gpu_request,
            "labels": job.metadata.labels or {}  # Include labels for identification
        }

        return description

    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"Job {job_id} not found in namespace {namespace}")
        else:
            raise RuntimeError(f"Error describing job: {str(e)}")


def get_kubernetes_contexts() -> List[Dict[str, Any]]:
    """
    Get available Kubernetes contexts.

    Returns:
        List of context dictionaries with name, cluster, and user
    """
    try:
        # Load Kubernetes configuration
        contexts, active_context = config.list_kube_config_contexts()

        # Format contexts
        formatted_contexts = []
        for ctx in contexts:
            formatted_contexts.append({
                "name": ctx["name"],
                "cluster": ctx["context"]["cluster"],
                "user": ctx["context"]["user"],
                "active": ctx == active_context
            })

        return formatted_contexts
    except Exception as e:
        console.print(f"[bold red]Error getting Kubernetes contexts:[/bold red] {str(e)}")
        return []


def set_kubernetes_context(context_name: str) -> bool:
    """
    Set the current Kubernetes context.

    Args:
        context_name: Name of the context to set

    Returns:
        True if successful, False otherwise
    """
    try:
        # Set the context
        config.load_kube_config(context=context_name)
        return True
    except Exception as e:
        console.print(f"[bold red]Error setting Kubernetes context:[/bold red] {str(e)}")
        return False


def check_namespace_exists(namespace: str) -> tuple[bool, Optional[str]]:
    """
    Check if a namespace exists and is accessible.

    Args:
        namespace: Name of the namespace to check

    Returns:
        Tuple of (exists, error_message):
        - exists: True if namespace exists and is accessible, False otherwise
        - error_message: Error message if failed, None if successful
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    core_api = client.CoreV1Api()

    try:
        # Check if namespace exists
        core_api.read_namespace(name=namespace)
        return True, None
    except ApiException as e:
        error_message = str(e)
        if e.status == 404:
            error_message = f"Namespace '{namespace}' does not exist. Please run 'ksub init' to create it."
        elif e.status == 403:
            error_message = f"You do not have permission to access namespace '{namespace}'. Please use a namespace you have access to or contact your cluster administrator."

        return False, error_message


def check_namespace_label(namespace: str, label_key: str, label_value: str) -> tuple[bool, Optional[str]]:
    """
    Check if a namespace has a specific label with a specific value.

    Args:
        namespace: Name of the namespace to check
        label_key: Key of the label to check
        label_value: Value of the label to check

    Returns:
        Tuple of (has_label, error_message):
        - has_label: True if namespace has the label with the specified value, False otherwise
        - error_message: Error message if failed, None if successful
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    core_api = client.CoreV1Api()

    try:
        # Check if namespace exists
        ns = core_api.read_namespace(name=namespace)

        # Check if namespace has the label with the specified value
        labels = ns.metadata.labels or {}
        if label_key in labels and labels[label_key] == label_value:
            return True, None
        else:
            return False, f"Namespace '{namespace}' does not have label '{label_key}={label_value}'."
    except ApiException as e:
        error_message = str(e)
        if e.status == 404:
            error_message = f"Namespace '{namespace}' does not exist."
        elif e.status == 403:
            error_message = f"You do not have permission to access namespace '{namespace}'."

        return False, error_message


def check_admin_storage_transfer_pod(admin_namespace: str = "ksub-admin") -> tuple[bool, Optional[str]]:
    """
    Check if the admin storage transfer pod exists and is running.

    Args:
        admin_namespace: Name of the admin namespace (default: ksub-admin)

    Returns:
        Tuple of (exists, error_message):
        - exists: True if admin storage transfer pod exists and is running, False otherwise
        - error_message: Error message if failed, None if successful
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    core_api = client.CoreV1Api()

    try:
        # Check if admin namespace exists
        try:
            core_api.read_namespace(name=admin_namespace)
        except ApiException as e:
            if e.status == 404:
                return False, f"Admin namespace '{admin_namespace}' does not exist."
            elif e.status == 403:
                return False, f"You do not have permission to access admin namespace '{admin_namespace}'."
            else:
                return False, f"Error accessing admin namespace: {str(e)}"

        # Check if admin storage transfer pod exists
        pods = core_api.list_namespaced_pod(
            namespace=admin_namespace,
            label_selector="app=ksub-storage-transfer"
        )

        if not pods.items:
            return False, f"No storage transfer pod found in admin namespace '{admin_namespace}'."

        # Check if at least one pod is running
        running_pods = [pod for pod in pods.items if pod.status.phase == "Running"]
        if not running_pods:
            return False, f"No running storage transfer pod found in admin namespace '{admin_namespace}'."

        return True, None
    except ApiException as e:
        error_message = str(e)
        return False, f"Error checking admin storage transfer pod: {error_message}"


def check_shared_volume_mounts(namespace: str) -> tuple[bool, Optional[str]]:
    """
    Check if shared volume mounts exist in the namespace.

    Args:
        namespace: Name of the namespace to check

    Returns:
        Tuple of (exists, error_message):
        - exists: True if shared volume mounts exist, False otherwise
        - error_message: Error message if failed, None if successful
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    core_api = client.CoreV1Api()

    try:
        # Check if namespace exists
        try:
            core_api.read_namespace(name=namespace)
        except ApiException as e:
            if e.status == 404:
                return False, f"Namespace '{namespace}' does not exist."
            elif e.status == 403:
                return False, f"You do not have permission to access namespace '{namespace}'."
            else:
                return False, f"Error accessing namespace: {str(e)}"

        # Check if shared volume mounts exist
        pvcs = core_api.list_namespaced_persistent_volume_claim(
            namespace=namespace,
            label_selector="ksub/role=scratch"
        )

        if not pvcs.items:
            return False, f"No shared volume mounts found in namespace '{namespace}'."

        return True, None
    except ApiException as e:
        error_message = str(e)
        return False, f"Error checking shared volume mounts: {error_message}"


def create_namespace(namespace: str) -> tuple[bool, Optional[str]]:
    """
    Create a Kubernetes namespace if it doesn't exist.

    Args:
        namespace: Name of the namespace to create

    Returns:
        Tuple of (success, error_message):
        - success: True if successful or already exists, False otherwise
        - error_message: Error message if failed, None if successful
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    core_api = client.CoreV1Api()

    try:
        # Check if namespace exists
        try:
            core_api.read_namespace(name=namespace)
            console.print(f"[yellow]Namespace {namespace} already exists[/yellow]")
            return True, None
        except ApiException as e:
            if e.status != 404:
                raise e

        # Create namespace
        namespace_manifest = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=namespace)
        )
        core_api.create_namespace(body=namespace_manifest)
        console.print(f"[green]Namespace {namespace} created successfully[/green]")
        return True, None
    except ApiException as e:
        error_message = str(e)
        print(e)
        if e.status == 403:
            error_message = f"You do not have permission to create namespace '{namespace}' in this cluster. Please contact your cluster administrator or use a namespace you have access to."
            console.print(f"[bold red]Error creating namespace:[/bold red] {error_message}")
            console.print(
                "[bold yellow]⚠️ ksub cannot continue without a valid namespace. No other commands will work.[/bold yellow]")
        else:
            console.print(f"[bold red]Error creating namespace:[/bold red] {error_message}")

        return False, error_message


def list_jobs(
    namespace: Optional[str] = None,
    status: Optional[str] = None,
    label: Optional[str] = None,
    limit: int = 100,
    update_storage: bool = True
) -> List[Dict[str, Any]]:
    """
    List jobs from Kubernetes.

    Args:
        namespace: Filter by namespace (default: current namespace)
        status: Filter by status (Running, Succeeded, Failed, etc.)
        label: Filter by label (format: key=value)
        limit: Maximum number of jobs to return
        update_storage: Whether to update local storage with job status

    Returns:
        List of job dictionaries with job details

    Raises:
        RuntimeError: If Kubernetes API cannot be accessed
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    batch_api = client.BatchV1Api()

    # Use current namespace if not specified
    if namespace is None:
        namespace = get_namespace()

    try:
        # Parse label selector if provided
        label_selector = None
        if label:
            # Label should be in format "key=value"
            if "=" in label:
                label_selector = label
            else:
                console.print(f"[bold yellow]Warning:[/bold yellow] Invalid label format: {label}. Expected format: key=value")

        # List jobs in namespace
        job_list = batch_api.list_namespaced_job(
            namespace=namespace,
            limit=limit,
            label_selector=label_selector
        )

        # Convert to list of dicts
        jobs = []
        for job in job_list.items:
            # Extract basic job information
            job_info = {
                "job_id": job.metadata.name,
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "created_at": job.metadata.creation_timestamp,
                "active": job.status.active or 0,
                "succeeded": job.status.succeeded or 0,
                "failed": job.status.failed or 0,
                "completion_time": job.status.completion_time,
                "labels": job.metadata.labels or {},
                "owner": job.metadata.labels.get("owner", "unknown") if job.metadata.labels else "unknown",
            }

            # Determine status
            if job.status.active:
                job_info["status"] = "Running"
            elif job.status.succeeded:
                job_info["status"] = "Succeeded"
            elif job.status.failed:
                job_info["status"] = "Failed"
            else:
                job_info["status"] = "Unknown"

            # Filter by status if specified
            if status and job_info["status"] != status:
                continue

            # Calculate age and duration
            created_at = job_info["created_at"]
            completion_time = job_info["completion_time"]

            if created_at:
                # Calculate age
                if completion_time:
                    duration_seconds = (completion_time - created_at).total_seconds()
                    from ksub.utils.formatting import format_duration
                    job_info["duration"] = format_duration(int(duration_seconds))

                # Calculate age from creation to now
                age_seconds = (time.time() - created_at.timestamp())
                from ksub.utils.formatting import format_duration
                job_info["age"] = format_duration(int(age_seconds))
            job_info["created_at"] = created_at
            if completion_time:
                job_info["completion_time"] = str(completion_time)
            jobs.append(job_info)

            # Update job status in local storage if requested
            if update_storage:
                update_job_status_in_storage(job_info)

        return jobs

    except ApiException as e:
        console.print(f"[bold red]Error listing jobs from Kubernetes:[/bold red] {str(e)}")
        return []


def update_job_status_in_storage(job_info: Dict[str, Any]) -> bool:
    """
    Update job status in local storage based on Kubernetes job status.

    Args:
        job_info: Job information dictionary from Kubernetes

    Returns:
        True if successful, False otherwise
    """
    from ksub.utils.storage import update_job_status, get_job

    job_id = job_info["job_id"]
    status = job_info["status"]
    completed = status in ["Succeeded", "Failed"]

    try:
        # Check if job exists in local storage
        existing_job = get_job(job_id)

        if existing_job:
            # Update job status if it has changed
            if existing_job["status"] != status:
                update_job_status(job_id, status, completed)
                console.print(f"[green]Updated status of job {job_id} to {status} in local storage[/green]")
            return True
        else:
            # Job doesn't exist in local storage, store it
            from ksub.utils.storage import store_job

            # Extract necessary information for storage
            store_job(
                job_id=job_id,
                name=job_info["name"],
                namespace=job_info["namespace"],
                status=status,
                owner=job_info["owner"],
                metadata={"labels": job_info["labels"]}
            )
            console.print(f"[green]Stored job {job_id} in local storage with status {status}[/green]")
            return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not update job {job_id} in local storage: {str(e)}[/yellow]")
        return False


def wait_for_job_completion(job_id: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Wait for a job to complete.

    Args:
        job_id: ID of the job
        timeout: Timeout in seconds (None for no timeout)

    Returns:
        Dict containing job status information

    Raises:
        RuntimeError: If job cannot be found or times out
    """
    # Initialize Kubernetes client
    initialize_kubernetes_client()

    # Create API client
    batch_api = client.BatchV1Api()

    namespace = get_namespace()

    try:
        # For now, we're assuming job_id is the job name
        # In a real implementation, we would look up the job by ID in our local database
        job_name = job_id

        # Set up watch
        w = watch.Watch()

        # Start time for timeout
        start_time = time.time()

        for event in w.stream(
                batch_api.list_namespaced_job,
                namespace=namespace,
                field_selector=f"metadata.name={job_name}",
                timeout_seconds=timeout
        ):
            job = event['object']

            # Check if job is complete
            if job.status.succeeded or job.status.failed:
                w.stop()
                return get_job_status(job_id)

            # Check timeout
            if timeout and (time.time() - start_time > timeout):
                w.stop()
                raise RuntimeError(f"Timeout waiting for job {job_id} to complete")

        # If we get here, the watch ended without the job completing
        raise RuntimeError(f"Watch ended before job {job_id} completed")

    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"Job {job_id} not found in namespace {namespace}")
        else:
            raise RuntimeError(f"Error waiting for job: {str(e)}")
