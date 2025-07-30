"""CLI interface for workflow management."""

import argparse
import sys
from pathlib import Path

from srunx.logging import configure_workflow_logging, get_logger
from srunx.models import Job, ShellJob, Workflow
from srunx.workflows.runner import WorkflowRunner

logger = get_logger(__name__)


def create_workflow_parser() -> argparse.ArgumentParser:
    """Create argument parser for workflow commands."""
    parser = argparse.ArgumentParser(
        description="Execute YAML-defined workflows using SLURM and Prefect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example YAML workflow:
  name: ml_pipeline
  tasks:
    - name: preprocess
      command: ["python", "preprocess.py"]
      nodes: 1

    - name: train
      command: ["python", "train.py"]
      depends_on: [preprocess]
      gpus_per_node: 1
      conda: ml_env

    - name: evaluate
      command: ["python", "evaluate.py"]
      depends_on: [train]

    - name: notify
      command: ["python", "notify.py"]
      depends_on: [train, evaluate]
      async: true
        """,
    )

    parser.add_argument(
        "yaml_file",
        type=str,
        help="Path to YAML workflow definition file",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the workflow file without executing",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running jobs",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: %(default)s)",
    )

    return parser


def cmd_run_workflow(args: argparse.Namespace) -> None:
    """Handle workflow execution command."""
    # Configure logging for workflow execution
    configure_workflow_logging(level=args.log_level)

    try:
        yaml_file = Path(args.yaml_file)
        if not yaml_file.exists():
            logger.error(f"Workflow file not found: {args.yaml_file}")
            sys.exit(1)

        runner = WorkflowRunner()

        # Load workflow for validation
        workflow = runner.load_from_yaml(yaml_file)
        logger.info(
            f"Loaded workflow '{workflow.name}' with {len(workflow.tasks)} tasks"
        )

        # Validate dependencies
        _validate_workflow_dependencies(workflow)

        if args.validate_only:
            logger.info("Workflow validation successful")
            return

        if args.dry_run:
            _show_workflow_plan(workflow)
            return

        # Execute workflow
        logger.info("Starting workflow execution")
        results = runner.execute_workflow(workflow)

        logger.info("Workflow execution completed successfully")
        logger.info("Job Results:")
        for task_name, job in results.items():
            if hasattr(job, "job_id") and job.job_id:
                logger.info(f"  {task_name}: Job ID {job.job_id}")
            else:
                logger.info(f"  {task_name}: {job}")

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        sys.exit(1)


def _validate_workflow_dependencies(workflow: Workflow) -> None:
    """Validate workflow task dependencies."""
    task_names = {task.name for task in workflow.tasks}

    for task in workflow.tasks:
        for dependency in task.depends_on:
            if dependency not in task_names:
                raise ValueError(
                    f"Task '{task.name}' depends on unknown task '{dependency}'"
                )

    # Check for circular dependencies (simple check)
    visited = set()
    rec_stack = set()

    def has_cycle(task_name: str) -> bool:
        if task_name in rec_stack:
            return True
        if task_name in visited:
            return False

        visited.add(task_name)
        rec_stack.add(task_name)

        task = workflow.get_task(task_name)
        if task:
            for dependency in task.depends_on:
                if has_cycle(dependency):
                    return True

        rec_stack.remove(task_name)
        return False

    for task in workflow.tasks:
        if has_cycle(task.name):
            raise ValueError(
                f"Circular dependency detected involving task '{task.name}'"
            )


def _show_workflow_plan(workflow: Workflow) -> None:
    """Show workflow execution plan."""
    msg = f"""\
Workflow execution plan:
    Workflow: {workflow.name}
    Tasks: {len(workflow.tasks)}
"""

    for task in workflow.tasks:
        msg += f"\t\tTask: {task.name}\n"
        if isinstance(task.job, Job):
            msg += f"\t\t\tCommand: {' '.join(task.job.command or [])}\n"
            msg += f"\t\t\tResources: {task.job.resources.nodes} nodes, {task.job.resources.gpus_per_node} GPUs/node\n"
            if task.job.environment.conda:
                msg += f"\t\t\tConda env: {task.job.environment.conda}\n"
            if task.job.environment.sqsh:
                msg += f"\t\t\tSqsh: {task.job.environment.sqsh}\n"
        elif isinstance(task.job, ShellJob):
            msg += f"\t\t\tPath: {task.job.path}\n"

        if task.depends_on:
            msg += f"\t\t\tDependencies: {', '.join(task.depends_on)}\n"
        if task.async_execution:
            msg += "\t\t\tExecution: asynchronous\n"

    logger.info(msg)


def main() -> None:
    """Main entry point for workflow CLI."""
    parser = create_workflow_parser()
    args = parser.parse_args()

    cmd_run_workflow(args)


if __name__ == "__main__":
    main()
