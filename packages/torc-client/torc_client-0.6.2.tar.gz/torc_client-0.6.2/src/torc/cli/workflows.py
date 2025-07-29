"""CLI commands to manage a workflow"""

import getpass
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

import json5
import rich_click as click
from loguru import logger

from torc import add_jobs, iter_documents
from torc.openapi_client import (
    JobModel,
    ResourceRequirementsModel,
    WorkflowModel,
    WorkflowSpecificationModel,
)
from torc.api import remove_db_keys, sanitize_workflow, list_model_fields
from torc.exceptions import InvalidWorkflow
from torc.hpc.slurm_interface import SlurmInterface
from torc.openapi_client.api import DefaultApi
from torc.workflow_manager import WorkflowManager
from .common import (
    check_database_url,
    confirm_change,
    get_workflow_key_from_context,
    get_output_format_from_context,
    get_user_from_context,
    prompt_user_for_workflow,
    setup_cli_logging,
    parse_filters,
    print_items,
)


@click.group()
def workflows():
    """Workflow commands"""


@click.command()
@click.argument("workflow_keys", nargs=-1)
@click.pass_obj
@click.pass_context
def cancel(ctx, api: DefaultApi, workflow_keys: tuple[str]) -> None:
    """Cancel one or more workflows."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    if not workflow_keys:
        workflow = prompt_user_for_workflow(ctx, api, auto_select_one_option=False)
        workflow_keys = [workflow.key]

    msg = "This command will cancel all specified workflows."
    confirm_change(ctx, msg)

    for key in workflow_keys:
        cancel_workflow(api, key)


@click.command()
@click.option(
    "-d",
    "--description",
    type=str,
    help="Workflow description",
)
@click.option(
    "-k",
    "--key",
    type=str,
    help="Workflow key. Default is to auto-generate",
)
@click.option(
    "-n",
    "--name",
    type=str,
    help="Workflow name",
)
@click.pass_obj
@click.pass_context
def create(
    ctx: click.Context,
    api: DefaultApi,
    description: str,
    key: str,
    name: str,
) -> None:
    """Create a new workflow."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow = WorkflowModel(
        description=description,
        _key=key,
        name=name,
        user=get_user_from_context(ctx),
    )
    output_format = get_output_format_from_context(ctx)
    workflow = api.add_workflow(workflow)
    if output_format == "text":
        logger.info("Created a workflow with key={}", workflow.key)
    else:
        print(json.dumps({"key": workflow.key}))


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "-c",
    "--cpus-per-job",
    default=1,
    show_default=True,
    type=int,
    help="Number of CPUs required for each job.",
)
@click.option(
    "-d",
    "--description",
    type=str,
    help="Workflow description",
)
@click.option(
    "-k",
    "--key",
    type=str,
    help="Workflow key. Default is to auto-generate",
)
@click.option(
    "-m",
    "--memory-per-job",
    default="1m",
    show_default=True,
    type=str,
    help="Amount of memory required for each job. Use '100m' for 100 MB, '1g' for 1 GB, etc.",
)
@click.option(
    "-n",
    "--name",
    type=str,
    help="Workflow name",
)
@click.option(
    "-r",
    "--runtime-per-job",
    default="P0DT1m",
    show_default=True,
    type=str,
    help="Runtime required for each job in ISO8601 format. Example: P0DT1H is one hour.",
)
@click.pass_obj
@click.pass_context
def create_from_commands_file(
    ctx: click.Context,
    api: DefaultApi,
    filename: Path,
    cpus_per_job: int,
    description: str,
    key: str,
    memory_per_job: str,
    name: str,
    runtime_per_job: str,
) -> None:
    """Create a workflow from a text file containing job CLI commands."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    output_format = get_output_format_from_context(ctx)
    commands = _read_jobs_from_commands_file(filename)
    workflow = WorkflowModel(
        description=description,
        _key=key,
        name=name,
        user=get_user_from_context(ctx),
    )
    workflow = api.add_workflow(workflow)
    assert workflow.key is not None
    if output_format == "text":
        logger.info("Created a workflow from {} with key={}", filename, workflow.key)
    else:
        print(json.dumps({"filename": filename, "key": workflow.key}))

    name = f"rr_{cpus_per_job}_{memory_per_job}_{runtime_per_job}"
    req = api.add_resource_requirements(
        workflow.key,
        ResourceRequirementsModel(
            name=name, num_cpus=cpus_per_job, memory=memory_per_job, runtime=runtime_per_job
        ),
    )
    jobs = [
        JobModel(name=str(i + 1), command=command, resource_requirements=req.id)
        for i, command in enumerate(commands)
    ]
    add_jobs(api, workflow.key, jobs)


@click.command()
@click.argument("filename", type=click.Path(exists=True))
@click.option(
    "-c",
    "--cpus-per-job",
    default=1,
    show_default=True,
    type=int,
    help="Number of CPUs required for each job.",
)
@click.option(
    "-m",
    "--memory-per-job",
    default="1m",
    show_default=True,
    type=str,
    help="Amount of memory required for each job. Use '100m' for 100 MB, '1g' for 1 GB, etc.",
)
@click.option(
    "-r",
    "--runtime-per-job",
    default="P0DT1m",
    show_default=True,
    type=str,
    help="Runtime required for each job in ISO8601 format. Example: P0DT1H is one hour.",
)
@click.pass_obj
@click.pass_context
def add_jobs_from_commands_file(
    ctx: click.Context,
    api: DefaultApi,
    filename: Path,
    cpus_per_job: int,
    memory_per_job: str,
    runtime_per_job: str,
) -> None:
    """Add jobs to a workflow from a text file containing job CLI commands."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    output_format = get_output_format_from_context(ctx)
    workflow_key = get_workflow_key_from_context(ctx, api)
    commands = _read_jobs_from_commands_file(filename)
    name = f"rr_{cpus_per_job}_{memory_per_job}_{runtime_per_job}"
    req = api.add_resource_requirements(
        workflow_key,
        ResourceRequirementsModel(
            name=name, num_cpus=cpus_per_job, memory=memory_per_job, runtime=runtime_per_job
        ),
    )
    res = api.list_jobs(workflow_key, limit=1)
    jobs = [
        JobModel(name=str(i), command=command, resource_requirements=req.id)
        for i, command in enumerate(commands, start=res.total_count + 1)
    ]
    add_jobs(api, workflow_key, jobs)

    if output_format == "text":
        logger.info("Added {} jobs to workflow {}", len(jobs), workflow_key)
    else:
        print(json.dumps({"num_jobs": len(jobs), "key": workflow_key}))


def _read_jobs_from_commands_file(filename: Path) -> list[str]:
    commands = []
    with open(filename, encoding="utf-8") as f_in:
        for line in f_in:
            line = line.strip()
            if line:
                commands.append(line)
    if not commands:
        msg = "No commands found in the {filename=}"
        raise InvalidWorkflow(msg)

    return commands


@click.command()
@click.argument("filename", type=click.Path(exists=True), callback=lambda *x: Path(x[2]))
@click.pass_obj
@click.pass_context
def create_from_json_file(ctx: click.Context, api: DefaultApi, filename: Path) -> None:
    """Create a workflow from a JSON/JSON5 file."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow = create_workflow_from_json_file(api, filename, user=get_user_from_context(ctx))

    output_format = get_output_format_from_context(ctx)
    if output_format == "text":
        logger.info("Created a workflow from {} with key={}", filename, workflow.key)
    else:
        print(json.dumps({"filename": str(filename), "key": workflow.key}))


@click.command()
@click.argument("workflow_key")
@click.option(
    "-a",
    "--archive",
    help="Set to 'true' to archive the workflow or 'false' to enable it.",
)
@click.option(
    "-d",
    "--description",
    type=str,
    help="Workflow description",
)
@click.option(
    "-n",
    "--name",
    type=str,
    help="Workflow name",
)
@click.pass_obj
@click.pass_context
def modify(
    ctx: click.Context,
    api: DefaultApi,
    workflow_key: str,
    archive: str,
    description: str,
    name: str,
) -> None:
    """Modify the workflow parameters."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow = api.get_workflow(workflow_key)
    if archive is not None:
        archive_lowered = archive.lower()
        if archive_lowered not in ("true", "false"):
            logger.error("--archive must be 'true' or 'false': {}", archive)
        workflow.is_archived = True if archive_lowered == "true" else False
    if description is not None:
        workflow.description = description
    if name is not None:
        workflow.name = name
    workflow.user = get_user_from_context(ctx)
    workflow = api.modify_workflow(workflow_key, workflow)
    logger.info("Updated workflow {}", workflow.key)


@click.command()
@click.argument("workflow_keys", nargs=-1)
@click.pass_obj
@click.pass_context
def delete(ctx: click.Context, api: DefaultApi, workflow_keys: tuple[str]):
    """Delete one or more workflows by key."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    if not workflow_keys:
        workflow = prompt_user_for_workflow(ctx, api, auto_select_one_option=False)
        workflow_keys = [workflow.key]

    _delete_workflows_with_warning(ctx, api, workflow_keys)


@click.command()
@click.pass_obj
@click.pass_context
def delete_all(ctx: click.Context, api: DefaultApi) -> None:
    """Delete all workflows stored by the user."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    user = get_user_from_context(ctx)
    keys = [x.key for x in iter_documents(api.list_workflows, user=user)]
    _delete_workflows_with_warning(ctx, api, keys)


def _delete_workflows_with_warning(
    ctx: click.Context, api: DefaultApi, keys: Iterable[str]
) -> None:
    items = [api.get_workflow(x).to_dict() for x in keys]
    columns = list_model_fields(WorkflowModel)
    columns.remove("_id")
    columns.remove("_rev")
    print_items(
        ctx,
        items,
        "Workflows",
        columns,
        "workflows",
    )
    msg = "This command will delete the workflows above. Continue?"
    confirm_change(ctx, msg)
    current_user = get_user_from_context(ctx)
    for i, key in enumerate(keys):
        user = items[i]["user"]
        if user != current_user:
            msg = f"Workflow {key} was created by {user=}, not {current_user=}. Continue?"
            confirm_change(ctx, msg)
        api.remove_workflow(key)
        logger.info("Deleted workflow {}", key)


@click.command()
@click.pass_obj
@click.pass_context
def list_scheduler_configs(ctx: click.Context, api: DefaultApi) -> None:
    """List the scheduler configs in the database."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    output_format = get_output_format_from_context(ctx)
    workflow_key = get_workflow_key_from_context(ctx, api)
    items = []
    for scheduler in ("aws_schedulers", "local_schedulers", "slurm_schedulers"):
        method = getattr(api, f"list_{scheduler}")
        for doc in iter_documents(method, workflow_key):
            items.append(doc.id)

    if output_format == "text":
        logger.info("Scheduler configs in workflow {}", workflow_key)
        for item in items:
            print(item)
    else:
        print(json.dumps({"ids": items}))


@click.command(name="list")
@click.option(
    "-A",
    "--only-archived",
    is_flag=True,
    default=False,
    show_default=True,
    help="List only workflows that have been archived.",
)
@click.option(
    "-i",
    "--include-archived",
    is_flag=True,
    default=False,
    show_default=True,
    help="Include archived workflows in the list.",
)
@click.option(
    "-a",
    "--all-users",
    is_flag=True,
    default=False,
    help="List workflows for all users. Default is only for the current user.",
)
@click.option(
    "-f",
    "--filters",
    multiple=True,
    type=str,
    help="Filter the values according to each key=value pair.",
)
@click.option(
    "--sort-by",
    type=str,
    help="Sort results by this column.",
)
@click.option(
    "--reverse-sort",
    is_flag=True,
    default=False,
    show_default=True,
    help="Reverse the sort order if --sort-by is set.",
)
@click.pass_obj
@click.pass_context
def list_workflows(
    ctx: click.Context,
    api: DefaultApi,
    only_archived: bool,
    include_archived: bool,
    all_users: bool,
    filters: tuple[str],
    sort_by: Optional[str],
    reverse_sort: bool,
):
    """List all workflows stored by the user.

    \b
    1. List all workflows for the current user in a table.
       $ torc workflows list
    2. List all workflows in JSON format.
       $ torc -o json workflows list
    3. List only archived workflows.
       $ torc workflows list --only-archived
    4. List all workflows for all users, including archived workflows.
       $ torc workflows list --all-users --include-archived
    """
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    table_title = "Workflows"
    if only_archived and include_archived:
        logger.error("Only one of --only-archived and --include-archived can be set.")
        sys.exit(1)
    _filters = parse_filters(filters)
    if sort_by is not None:
        _filters["sort_by"] = sort_by
        _filters["reverse_sort"] = reverse_sort
    if not include_archived:
        _filters["is_archived"] = only_archived
    if not all_users:
        _filters["user"] = get_user_from_context(ctx)
    items = (x.to_dict() for x in iter_documents(api.list_workflows, **_filters))
    columns = list_model_fields(WorkflowModel)
    columns.remove("_id")
    columns.remove("_rev")
    print_items(
        ctx,
        items,
        table_title,
        columns,
        "workflows",
    )


@click.command()
@click.pass_obj
@click.pass_context
def process_auto_tune_resource_requirements_results(ctx: click.Context, api: DefaultApi) -> None:
    """Process the results of the first round of auto-tuning resource requirements."""
    setup_cli_logging(ctx, __name__)
    workflow_key = get_workflow_key_from_context(ctx, api)
    api.process_auto_tune_resource_requirements_results(workflow_key)
    url = api.api_client.configuration.host
    rr_cmd = f"torc -k {workflow_key} -u {url} resource-requirements list"
    events_cmd = f"torc -k {workflow_key} -u {url} events list -f category=resource_requirements"
    logger.info(
        "Updated resource requirements. Look at current requirements with "
        "\n  '{}'\n and at "
        "changes by reading the events with \n  '{}'\n",
        rr_cmd,
        events_cmd,
    )


@click.command()
@click.argument("workflow_keys", nargs=-1)
@click.option(
    "-f",
    "--failed-only",
    is_flag=True,
    default=False,
    show_default=True,
    help="Only reset the status of failed jobs.",
)
@click.option(
    "-r",
    "--restart",
    is_flag=True,
    default=False,
    show_default=True,
    help="Send the 'workflows restart' command after resetting status.",
)
@click.pass_obj
@click.pass_context
def reset_status(
    ctx: click.Context,
    api: DefaultApi,
    workflow_keys: tuple[str],
    failed_only: bool,
    restart: bool,
) -> None:
    """Reset the status of the workflow(s) and all jobs."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    if workflow_keys:
        workflows = [api.get_workflow(x) for x in workflow_keys]
    else:
        workflows = [prompt_user_for_workflow(ctx, api, auto_select_one_option=False)]

    for workflow in workflows:
        assert workflow.key is not None
        msg = f"""This command will reset the status of this workflow:
        key: {workflow.key}
        user: {workflow.user}
        name: {workflow.name}
        description: {workflow.description}
        """
        if restart:
            msg += "\nAfter resetting status this command will restart the workflow."
        confirm_change(ctx, msg)
        reset_workflow_status(api, workflow.key)
        reset_workflow_job_status(api, workflow.key, failed_only=failed_only)
        if restart:
            restart_workflow(api, workflow.key)


@click.command()
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Perform a dry run. Show status changes but do not change any database values.",
)
@click.option(
    "-i",
    "--ignore-missing-data",
    is_flag=True,
    default=False,
    show_default=True,
    help="Ignore checks for missing files and user data documents.",
)
@click.option(
    "--only-uninitialized",
    is_flag=True,
    default=False,
    show_default=True,
    help="Only initialize jobs with a status of uninitialized.",
)
@click.pass_obj
@click.pass_context
def restart(
    ctx: click.Context,
    api: DefaultApi,
    dry_run: bool,
    ignore_missing_data: bool,
    only_uninitialized: bool,
) -> None:
    """Restart the workflow defined in the database specified by the URL. Resets all jobs with
    a status of canceled, submitted, submitted_pending, and terminated. Does not affect jobs with
    a status of done unless an input file has changed.
    """
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow_key = get_workflow_key_from_context(ctx, api)
    _exit_if_jobs_are_running(api, workflow_key)
    workflow = api.get_workflow(workflow_key)
    types = "uninitialized" if only_uninitialized else "failed/incomplete"
    msg = f"""This command will restart this workflow and reset {types} job statuses.
    key: {workflow_key}
    user: {workflow.user}
    name: {workflow.name}
    description: {workflow.description}
"""
    confirm_change(ctx, msg, dry_run=dry_run)
    restart_workflow(
        api,
        workflow_key,
        ignore_missing_data=ignore_missing_data,
        only_uninitialized=only_uninitialized,
        dry_run=dry_run,
    )


@click.command()
@click.option(
    "-a",
    "--auto-tune-resource-requirements",
    is_flag=True,
    default=False,
    show_default=True,
    help="Setup the workflow such that only one job from each resource group is run in the first "
    "round. Upon completion torc will look at actual resource utilization of those jobs and "
    "apply the results to the resource requirements definitions. When jobs finish, please call "
    "'torc workflows process_auto_tune_resource_requirements_results' to update the requirements.",
)
@click.option(
    "-i",
    "--ignore-missing-data",
    is_flag=True,
    default=False,
    show_default=True,
    help="Ignore checks for missing files and user data documents.",
)
@click.pass_obj
@click.pass_context
def start(
    ctx: click.Context,
    api: DefaultApi,
    auto_tune_resource_requirements: bool,
    ignore_missing_data: bool,
) -> None:
    """Start the workflow defined in the database specified by the URL."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow_key = get_workflow_key_from_context(ctx, api)
    _exit_if_jobs_are_running(api, workflow_key)
    done_jobs = api.list_jobs(workflow_key, status="done", limit=1).items
    if done_jobs:
        workflow = api.get_workflow(workflow_key)
        msg = f"""This workflow has one or more jobs with a status of 'done.' This command will
reset all job statuses to 'uninitialized' and then 'ready' or 'blocked.'
    key: {workflow_key}
    user: {workflow.user}
    name: {workflow.name}
    description: {workflow.description}
"""
        confirm_change(ctx, msg)

    try:
        start_workflow(
            api,
            workflow_key,
            auto_tune_resource_requirements=auto_tune_resource_requirements,
            ignore_missing_data=ignore_missing_data,
        )
    except InvalidWorkflow as exc:
        logger.error("Invalid workflow: {}", exc)
        sys.exit(1)


# The functions below exist apart from the CLI functions so that the TUI can call them.


def create_workflow_from_json_file(
    api: DefaultApi, filename: Path, user: str = getpass.getuser()
) -> WorkflowModel:
    """Create a workflow from a JSON/JSON5 file."""
    method = json5.load if filename.suffix == ".json5" else json.load
    with open(filename, "r", encoding="utf-8") as f:
        data = sanitize_workflow(method(f))
    if data.get("user") != user:
        if "user" in data:
            logger.info("Overriding user={} with {}", data["user"], user)
        data["user"] = user
    name_to_file = {x["name"]: x for x in data.get("files", [])}
    for job in data["jobs"]:
        for field in ("input_files", "output_files"):
            args: list[str] = []
            for i, iofile in enumerate(job.get(field, [])):
                if isinstance(iofile, dict):
                    name = iofile["name"]
                    file_obj = name_to_file[name]
                    cli_arg = iofile.get("cli_arg", "")
                    if cli_arg:
                        path = file_obj["path"]
                        args.append(f"{cli_arg}={path}")
                    job[field][i] = name
            if args:
                job["command"] += f" {' '.join(args)}"

    spec = WorkflowSpecificationModel(**data)
    return api.add_workflow_specification(spec)


def start_workflow(
    api: DefaultApi,
    workflow_key: str,
    auto_tune_resource_requirements: bool = False,
    ignore_missing_data: bool = False,
) -> None:
    """Starts the workflow."""
    mgr = WorkflowManager(api, workflow_key)
    mgr.start(
        auto_tune_resource_requirements=auto_tune_resource_requirements,
        ignore_missing_data=ignore_missing_data,
    )
    # TODO: This could schedule nodes.


def restart_workflow(
    api: DefaultApi,
    workflow_key: str,
    only_uninitialized: bool = False,
    ignore_missing_data: bool = False,
    dry_run: bool = False,
) -> None:
    """Restarts the workflow."""
    mgr = WorkflowManager(api, workflow_key)
    mgr.restart(
        ignore_missing_data=ignore_missing_data,
        only_uninitialized=only_uninitialized,
        dry_run=dry_run,
    )
    api.add_event(
        workflow_key,
        {
            "category": "workflow",
            "type": "restart",
            "key": workflow_key,
            "message": f"Restarted workflow {workflow_key}",
        },
    )
    # TODO: This could schedule nodes.


def reset_workflow_status(api: DefaultApi, workflow_key: str) -> None:
    """Resets the status of the workflow."""
    api.reset_workflow_status(workflow_key)
    logger.info("Reset workflow status")
    api.add_event(
        workflow_key,
        {
            "category": "workflow",
            "type": "reset_status",
            "key": workflow_key,
            "message": f"Reset workflow {workflow_key}",
        },
    )


def reset_workflow_job_status(api: DefaultApi, workflow_key: str, failed_only: bool = False):
    """Resets the status of the workflow jobs."""
    api.reset_job_status(workflow_key, failed_only=failed_only)
    logger.info("Reset job status, failed_only={}", failed_only)
    api.add_event(
        workflow_key,
        {
            "category": "workflow",
            "type": "reset_job_status",
            "key": workflow_key,
            "message": f"Reset workflow {workflow_key} job status",
        },
    )


def cancel_workflow(api: DefaultApi, workflow_key: str) -> None:
    """Cancels the workflow."""
    # TODO: Handling different scheduler types needs to be at a lower level.
    items = api.list_scheduled_compute_nodes(workflow_key).items
    assert items is not None
    for job in items:
        if (
            job.status != "complete"
            and job.scheduler_config_id.split("/")[0].split("__")[0] == "slurm_schedulers"
            and job.scheduler_id is not None
        ):
            assert job.key is not None
            intf = SlurmInterface()
            return_code = intf.cancel_job(job.scheduler_id)
            if return_code == 0:
                job.status = "complete"
                api.modify_scheduled_compute_node(workflow_key, job.key, job)
            # else: Ignore all return codes and try to cancel all jobs.
    api.cancel_workflow(workflow_key)
    logger.info("Canceled workflow {}", workflow_key)
    api.add_event(
        workflow_key,
        {
            "category": "workflow",
            "type": "cancel",
            "key": workflow_key,
            "message": f"Canceled workflow {workflow_key}",
        },
    )


def has_running_jobs(api: DefaultApi, workflow_key: str) -> bool:
    """Returns True if jobs are running."""
    submitted = api.list_jobs(workflow_key, status="submitted", limit=1)
    assert submitted.items is not None
    sub_pend = api.list_jobs(workflow_key, status="submitted_pending", limit=1)
    assert sub_pend.items is not None
    return len(submitted.items) > 0 or len(sub_pend.items) > 0


def _exit_if_jobs_are_running(api: DefaultApi, workflow_key: str) -> None:
    if has_running_jobs(api, workflow_key):
        logger.error(
            "This operation is not allowed on a workflow with 'submitted' jobs. Please allow "
            "the jobs to finish or cancel them."
        )
        sys.exit(1)


@click.command()
@click.option(
    "--sanitize/--no-santize",
    default=True,
    is_flag=True,
    show_default=True,
    help="Remove all database fields from workflow objects.",
)
@click.pass_obj
@click.pass_context
def show(ctx: click.Context, api: DefaultApi, sanitize: bool) -> None:
    """Show the workflow."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow_key = get_workflow_key_from_context(ctx, api)
    data = api.get_workflow_specification(workflow_key).to_dict()
    if sanitize:
        sanitize_workflow(data)
    print(json.dumps(data, indent=2))


@click.command()
@click.option(
    "-e",
    "--expiration-buffer",
    type=int,
    help="Set the number of seconds before the expiration time at which torc will terminate jobs.",
)
@click.option(
    "-h",
    "--wait-for-healthy-db",
    type=int,
    help="Set the number of minutes that torc will tolerate an offline database.",
)
@click.option(
    "-i",
    "--ignore-workflow-completion",
    type=str,
    help="Set to 'true' to cause torc to ignore workflow completions and hold onto compute node "
    "allocations indefinitely. Useful for debugging failed jobs. Set to 'false' to revert to "
    "the default behavior.",
)
@click.option(
    "-w",
    "--wait-for-new-jobs",
    type=int,
    help="Set the number of seconds that torc will wait for new jobs before exiting. Does not "
    "apply if the workflow is complete.",
)
@click.pass_obj
@click.pass_context
def set_compute_node_parameters(
    ctx: click.Context,
    api: DefaultApi,
    expiration_buffer: int,
    wait_for_healthy_db: bool,
    ignore_workflow_completion: str,
    wait_for_new_jobs: bool,
) -> None:
    """Set parameters that control how the torc worker app behaves on compute nodes.
    Run 'torc workflows show-config' to see the current values."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow_key = get_workflow_key_from_context(ctx, api)
    config = api.get_workflow_config(workflow_key)
    changed = False
    if (
        expiration_buffer is not None
        and expiration_buffer != config.compute_node_expiration_buffer_seconds
    ):
        config.compute_node_expiration_buffer_seconds = expiration_buffer
        changed = True
    if (
        wait_for_healthy_db is not None
        and wait_for_healthy_db != config.compute_node_wait_for_healthy_database_minutes
    ):
        config.compute_node_wait_for_healthy_database_minutes = wait_for_healthy_db
        changed = True
    if ignore_workflow_completion is not None:
        lowered = ignore_workflow_completion.lower()
        if lowered not in ("true", "false"):
            logger.error(
                "Invalid value for ignore_workflow_completion: {}", ignore_workflow_completion
            )
            sys.exit(1)
        val = lowered == "true"
        if val != config.compute_node_ignore_workflow_completion:
            config.compute_node_ignore_workflow_completion = val
            changed = True
    if (
        wait_for_new_jobs is not None
        and wait_for_new_jobs != config.compute_node_wait_for_new_jobs_seconds
    ):
        config.compute_node_wait_for_new_jobs_seconds = wait_for_new_jobs
        changed = True

    if changed:
        config = api.modify_workflow_config(workflow_key, config)
        print(json.dumps(config.to_dict(), indent=2))
    else:
        logger.warning("No parameters were changed")


@click.command()
@click.pass_obj
@click.pass_context
def show_config(ctx: click.Context, api: DefaultApi) -> None:
    """Show the workflow config."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow_key = get_workflow_key_from_context(ctx, api)
    config = api.get_workflow_config(workflow_key)
    print(json.dumps(config.to_dict(), indent=2))


@click.command()
@click.pass_obj
@click.pass_context
def show_status(ctx: click.Context, api: DefaultApi) -> None:
    """Show the workflow status."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    workflow_key = get_workflow_key_from_context(ctx, api)
    status = api.get_workflow_status(workflow_key)
    print(json.dumps(status.to_dict(), indent=2))


@click.command()
@click.pass_obj
@click.pass_context
def example(ctx: click.Context, api: DefaultApi) -> None:
    """Show the example workflow."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    data = api.get_workflow_specification_example().to_dict()
    sanitize_workflow(data)
    print(json.dumps(data, indent=2))


@click.command()
@click.pass_obj
@click.pass_context
def template(ctx: click.Context, api: DefaultApi) -> None:
    """Show the workflow template."""
    setup_cli_logging(ctx, __name__)
    check_database_url(api)
    data = api.get_workflow_specification_template().to_dict()
    data = remove_db_keys(data)
    data["config"] = remove_db_keys(data["config"])
    data.pop("key", None)
    print(json.dumps(data, indent=2))


workflows.add_command(cancel)
workflows.add_command(create)
workflows.add_command(create_from_commands_file)
workflows.add_command(add_jobs_from_commands_file)
workflows.add_command(create_from_json_file)
workflows.add_command(modify)
workflows.add_command(delete)
workflows.add_command(delete_all)
workflows.add_command(list_scheduler_configs)
workflows.add_command(list_workflows)
workflows.add_command(process_auto_tune_resource_requirements_results)
workflows.add_command(reset_status)
workflows.add_command(restart)
workflows.add_command(set_compute_node_parameters)
workflows.add_command(start)
workflows.add_command(show)
workflows.add_command(show_config)
workflows.add_command(show_status)
workflows.add_command(example)
workflows.add_command(template)
