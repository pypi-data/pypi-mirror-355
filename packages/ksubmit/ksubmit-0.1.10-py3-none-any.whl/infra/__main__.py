import re

import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as k8s
from pulumi import Config, export

config = Config()
mode = config.get("mode", "unknown").lower()
project = config.require("project")
region = config.get("region") or "us-central1"
bucket_name = config.require("bucketName")
k8s_provider = k8s.Provider("k8s")


def validate_email(email: str) -> bool:
    """
    Validate that the email address is in a valid format.

    Args:
        email: Email address to validate

    Returns:
        True if the email is valid, False otherwise
    """
    # Simple regex for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


if mode not in {"admin", "user"}:
    raise ValueError("Invalid mode specified. Use 'admin' or 'user'.")

if mode == "admin":
    pulumi.log.info("Running in admin mode. Setting up infrastructure for KSubmit.")

    sa = gcp.serviceaccount.Account("ksubStorageAccess",
                                    account_id="ksub-storage-access",
                                    display_name="KSubmit Storage Access Service Account",
                                    project=project)

    bucket = gcp.storage.Bucket(bucket_name,
                                location=region,
                                project=project)

    bucket_iam = gcp.storage.BucketIAMMember("bucketAccess",
                                             bucket=bucket.name,
                                             role="roles/storage.objectAdmin",
                                             member=sa.email.apply(lambda email: f"serviceAccount:{email}"))

    ns = k8s.core.v1.Namespace("ksubmitAdmin",
                               metadata={"name": "ksubmit-admin"},
                               opts=pulumi.ResourceOptions(provider=k8s_provider))

    k8s_sa = k8s.core.v1.ServiceAccount("default",
                                        metadata={
                                            "name": "default",
                                            "namespace": ns.metadata["name"],
                                            "annotations": {
                                                "iam.gke.io/gcp-service-account": sa.email,
                                            },
                                        },
                                        opts=pulumi.ResourceOptions(provider=k8s_provider))

    workload_identity_binding = gcp.projects.IAMMember("workloadIdentityBinding",
                                                       project=project,
                                                       role="roles/iam.workloadIdentityUser",
                                                       member=pulumi.Output.concat("serviceAccount:", project,
                                                                                   ".svc.id.goog[", ns.metadata["name"],
                                                                                   "/", k8s_sa.metadata["name"], "]"))

    pv = k8s.core.v1.PersistentVolume("ksubmitScratchCloudPv",
                                      metadata={
                                          "name": "ksubmit-scratch-cloud-pv",
                                          "labels": {"ksubmit/role": "shared"},
                                      },
                                      spec={
                                          "capacity": {"storage": "1000Ti"},
                                          "accessModes": ["ReadWriteMany"],
                                          "persistentVolumeReclaimPolicy": "Retain",
                                          "storageClassName": "",
                                          "csi": {
                                              "driver": "gcsfuse.csi.storage.gke.io",
                                              "volumeHandle": bucket_name,
                                          },
                                          "mountOptions": ["implicit-dirs", "uid=1000", "gid=1000"],
                                      },
                                      opts=pulumi.ResourceOptions(provider=k8s_provider))

    pvc = k8s.core.v1.PersistentVolumeClaim("ksubmitScratchCloudPvc",
                                            metadata={
                                                "name": "ksubmit-scratch-cloud-pvc",
                                                "namespace": ns.metadata["name"],
                                                "labels": {"ksubmit/role": "scratch"},
                                            },
                                            spec={
                                                "accessModes": ["ReadWriteMany"],
                                                "storageClassName": "",
                                                "resources": {"requests": {"storage": "1Ti"}},
                                                "volumeName": pv.metadata["name"],
                                            },
                                            opts=pulumi.ResourceOptions(provider=k8s_provider))

    deployment = k8s.apps.v1.Deployment("ksubmitStorageTransfer",
                                        metadata={
                                            "name": "ksubmit-storage-transfer",
                                            "namespace": ns.metadata["name"],
                                            "labels": {"app": "ksubmit-storage-transfer",
                                                       "purpose": "ksubmit-infrastructure"},
                                        },
                                        spec={
                                            "replicas": 1,
                                            "strategy": {"type": "Recreate"},
                                            "selector": {"matchLabels": {"app": "ksubmit-storage-transfer"}},
                                            "template": {
                                                "metadata": {
                                                    "labels": {"app": "ksubmit-storage-transfer",
                                                               "purpose": "ksubmit-infrastructure"},
                                                    "annotations": {"gke-gcsfuse/volumes": "true"},
                                                },
                                                "spec": {
                                                    "containers": [{
                                                        "name": "storage-transfer-helper",
                                                        "image": "bitnami/kubectl:latest",
                                                        "securityContext": {"runAsUser": 1000, "runAsGroup": 1000},
                                                        "command": ["/bin/sh"],
                                                        "args": ["-c", "sleep infinity"],
                                                        "volumeMounts": [{
                                                            "name": "scratch-space-cloud-pvc",
                                                            "mountPath": "/mnt/cloud/scratch",
                                                        }],
                                                        "resources": {
                                                            "requests": {"cpu": "100m", "memory": "128Mi"},
                                                            "limits": {"cpu": "500m", "memory": "512Mi"},
                                                        },
                                                    }],
                                                    "volumes": [{
                                                        "name": "scratch-space-cloud-pvc",
                                                        "persistentVolumeClaim": {"claimName": pvc.metadata["name"]},
                                                    }],
                                                },
                                            },
                                        },
                                        opts=pulumi.ResourceOptions(provider=k8s_provider))

    export("serviceAccountEmail", sa.email)
    export("bucketUrl", pulumi.Output.concat("gs://", bucket.name))
    export("namespace", ns.metadata["name"])

    export("persistentVolumeName", pv.metadata["name"])
    export("persistentVolumeClaimName", pvc.metadata["name"])

if mode == "user":
    username = config.require("username").lower()
    user_email = config.require("user_email").lower()
    bucket_name = config.require("bucketName")
    pulumi.log.info(f"Running in user mode for user: {username} with email: {user_email}")

    if not validate_email(user_email):
        raise ValueError(f"Invalid email format: {user_email}. Please provide a valid email address.")

    ns = k8s.core.v1.Namespace(username,
                               metadata={
                                   "name": username,
                                   "labels": {
                                       "ksubmit/email": user_email.replace("@", "_"),
                                   }
                               }, opts=pulumi.ResourceOptions(provider=k8s_provider))

    pv = k8s.core.v1.PersistentVolume(f"ksubmit-scratch-pv-{username}",
                                      metadata={
                                          "name": f"ksubmit-scratch-cloud-pv-{username}",
                                          "labels": {"ksubmit/role": "scratch"},
                                      },
                                      spec={
                                          "capacity": {"storage": "1Ti"},
                                          "accessModes": ["ReadWriteMany"],
                                          "persistentVolumeReclaimPolicy": "Retain",
                                          "storageClassName": "standard-rwo",
                                          "csi": {
                                              "driver": "gcsfuse.csi.storage.gke.io",
                                              "volumeHandle": f"{bucket_name}/{username}",
                                              "readOnly": False,
                                          },
                                          "mountOptions": ["implicit-dirs", "uid=1000", "gid=1000"],
                                      },
                                      opts=pulumi.ResourceOptions(provider=k8s_provider))

    pvc = k8s.core.v1.PersistentVolumeClaim(f"ksubmit-scratch-pvc-{username}",
                                            metadata={
                                                "name": "ksubmit-shared-cloud-pvc",
                                                "namespace": ns.metadata["name"],
                                                "labels": {"ksubmit/role": "scratch"},
                                            },
                                            spec={
                                                "accessModes": ["ReadWriteMany"],
                                                "storageClassName": "standard-rwo",
                                                "resources": {"requests": {"storage": "1Ti"}},
                                                "volumeName": pv.metadata["name"],
                                            },
                                            opts=pulumi.ResourceOptions(provider=k8s_provider))
