"""
Database utilities for ksubmit.

This module provides functions for interacting with the ksubmit database,
which is used to store job-to-submission mappings and other metadata.
"""
import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

def get_database_path() -> Path:
    """Get the path to the ksubmit database file."""
    ksub_dir = Path.home() / ".ksubmit"
    ksub_dir.mkdir(exist_ok=True)
    return ksub_dir / "ksubmit.db"

def get_database_connection() -> sqlite3.Connection:
    """Get a connection to the ksubmit database."""
    db_path = get_database_path()
    conn = sqlite3.connect(str(db_path))
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database() -> None:
    """Initialize the ksubmit database schema."""
    conn = get_database_connection()
    cursor = conn.cursor()

    # Create job_submissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_submissions (
        job_id TEXT PRIMARY KEY,
        submission_id TEXT NOT NULL,
        job_name TEXT NOT NULL,
        submit_time TIMESTAMP NOT NULL,
        status TEXT DEFAULT 'submitted',
        completion_time TIMESTAMP,
        exit_code INTEGER,
        metadata TEXT,  -- JSON string for additional metadata
        UNIQUE(job_id)
    )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submission_id ON job_submissions(submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON job_submissions(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_name ON job_submissions(job_name)")

    conn.commit()
    conn.close()

def store_job_submission_mapping(job_id: str, submission_id: str, job_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Store job-to-submission mapping with additional metadata.

    Args:
        job_id: The ID of the job
        submission_id: The ID of the submission
        job_name: The name of the job
        metadata: Additional metadata to store with the job
    """
    # Initialize database if it doesn't exist
    initialize_database()

    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        # Store basic mapping
        cursor.execute(
            "INSERT INTO job_submissions (job_id, submission_id, job_name, submit_time, metadata) VALUES (?, ?, ?, ?, ?)",
            (job_id, submission_id, job_name, datetime.now().isoformat(), json.dumps(metadata or {}))
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Handle case where job_id already exists
        cursor.execute(
            "UPDATE job_submissions SET submission_id = ?, job_name = ?, metadata = ? WHERE job_id = ?",
            (submission_id, job_name, json.dumps(metadata or {}), job_id)
        )
        conn.commit()
    finally:
        conn.close()

def get_jobs_for_submission(submission_id: str) -> List[Tuple[str, str]]:
    """
    Get all job IDs associated with a submission ID.

    Args:
        submission_id: The ID of the submission

    Returns:
        A list of tuples containing (job_id, job_name) for all jobs in the submission
    """
    # Initialize database if it doesn't exist
    initialize_database()

    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT job_id, job_name FROM job_submissions WHERE submission_id = ?",
        (submission_id,)
    )
    jobs = cursor.fetchall()
    conn.close()

    return jobs

def update_job_status(job_id: str, status: str, exit_code: Optional[int] = None) -> None:
    """
    Update the status of a job.

    Args:
        job_id: The ID of the job
        status: The new status of the job
        exit_code: The exit code of the job (if completed)
    """
    # Initialize database if it doesn't exist
    initialize_database()

    conn = get_database_connection()
    cursor = conn.cursor()

    if status in ["completed", "failed"]:
        cursor.execute(
            "UPDATE job_submissions SET status = ?, completion_time = ?, exit_code = ? WHERE job_id = ?",
            (status, datetime.now().isoformat(), exit_code, job_id)
        )
    else:
        cursor.execute(
            "UPDATE job_submissions SET status = ? WHERE job_id = ?",
            (status, job_id)
        )

    conn.commit()
    conn.close()

def get_job_submission_info(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a job submission.

    Args:
        job_id: The ID of the job

    Returns:
        A dictionary containing information about the job submission, or None if not found
    """
    # Initialize database if it doesn't exist
    initialize_database()

    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT job_id, submission_id, job_name, submit_time, status, completion_time, exit_code, metadata FROM job_submissions WHERE job_id = ?",
        (job_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "job_id": row[0],
        "submission_id": row[1],
        "job_name": row[2],
        "submit_time": row[3],
        "status": row[4],
        "completion_time": row[5],
        "exit_code": row[6],
        "metadata": json.loads(row[7]) if row[7] else {}
    }

def get_all_submissions() -> List[Dict[str, Any]]:
    """
    Get all unique submission IDs with their associated job counts and timestamps.

    Returns:
        A list of dictionaries containing submission information
    """
    # Initialize database if it doesn't exist
    initialize_database()

    conn = get_database_connection()
    cursor = conn.cursor()

    # Query to get all unique submission IDs with job counts and earliest submit time
    cursor.execute("""
        SELECT 
            submission_id, 
            COUNT(job_id) as job_count, 
            MIN(submit_time) as first_submit_time,
            GROUP_CONCAT(DISTINCT job_name) as job_names
        FROM job_submissions 
        GROUP BY submission_id 
        ORDER BY first_submit_time DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    submissions = []
    for row in rows:
        submissions.append({
            "run_id": row[0],
            "job_count": row[1],
            "submit_time": row[2],
            "job_names": row[3].split(',') if row[3] else []
        })

    return submissions
