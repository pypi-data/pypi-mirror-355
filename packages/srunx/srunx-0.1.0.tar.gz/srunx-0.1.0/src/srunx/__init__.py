"""srunx - Python library for SLURM job management."""

__author__ = "ksterx"
__description__ = "Python library for SLURM workload manager integration"

# Main public API
from .client import Slurm, cancel_job, retrieve_job, submit_job
from .logging import (
    configure_cli_logging,
    configure_logging,
    configure_workflow_logging,
    get_logger,
)
from .models import (
    Job,
    JobEnvironment,
    JobResource,
    JobStatus,
    Workflow,
    WorkflowTask,
    render_job_script,
)
from .workflows import WorkflowRunner, submit_and_monitor_job

__all__ = [
    # Client
    "Slurm",
    "submit_job",
    "retrieve_job",
    "cancel_job",
    # Models
    "Job",
    "JobResource",
    "JobEnvironment",
    "JobStatus",
    "Workflow",
    "WorkflowTask",
    "render_job_script",
    # Workflows
    "WorkflowRunner",
    "submit_and_monitor_job",
    # Logging
    "configure_logging",
    "configure_cli_logging",
    "configure_workflow_logging",
    "get_logger",
]
