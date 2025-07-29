from typing import Dict
from typing import List
from typing import Optional

import click

from tecton import tecton_context
from tecton._internals.infra_operations import create_feature_server_cache
from tecton._internals.infra_operations import create_feature_server_group
from tecton._internals.infra_operations import create_ingest_server_group
from tecton._internals.infra_operations import create_transform_server_group
from tecton._internals.infra_operations import delete_feature_server_cache
from tecton._internals.infra_operations import delete_feature_server_group
from tecton._internals.infra_operations import delete_ingest_server_group
from tecton._internals.infra_operations import delete_transform_server_group
from tecton._internals.infra_operations import get_feature_server_cache
from tecton._internals.infra_operations import get_feature_server_group
from tecton._internals.infra_operations import get_ingest_server_group
from tecton._internals.infra_operations import get_realtime_logs
from tecton._internals.infra_operations import get_transform_server_group
from tecton._internals.infra_operations import list_feature_server_caches
from tecton._internals.infra_operations import list_feature_server_groups
from tecton._internals.infra_operations import list_ingest_server_groups
from tecton._internals.infra_operations import list_transform_server_groups
from tecton._internals.infra_operations import update_feature_server_cache
from tecton._internals.infra_operations import update_feature_server_group
from tecton._internals.infra_operations import update_ingest_server_group
from tecton._internals.infra_operations import update_transform_server_group
from tecton.cli import printer
from tecton.cli.cli_utils import click_exception_wrapper
from tecton.cli.cli_utils import display_table
from tecton.cli.cli_utils import timestamp_to_string
from tecton.cli.command import TectonCommand
from tecton.cli.command import TectonCommandCategory
from tecton.cli.command import TectonGroup
from tecton_proto.servergroupservice.server_group_service__client_pb2 import AutoscalingConfig
from tecton_proto.servergroupservice.server_group_service__client_pb2 import FeatureServerCache
from tecton_proto.servergroupservice.server_group_service__client_pb2 import FeatureServerGroup
from tecton_proto.servergroupservice.server_group_service__client_pb2 import GetRealtimeLogsResponse
from tecton_proto.servergroupservice.server_group_service__client_pb2 import IngestServerGroup
from tecton_proto.servergroupservice.server_group_service__client_pb2 import ProvisionedScalingConfig
from tecton_proto.servergroupservice.server_group_service__client_pb2 import Status
from tecton_proto.servergroupservice.server_group_service__client_pb2 import TransformServerGroup


INFO_SIGN = "💡"


def _get_validated_workspace(workspace_name: Optional[str]) -> str:
    """Gets the workspace name, falling back to current context, and exits if none is found."""
    workspace = workspace_name or tecton_context.get_current_workspace()
    if not workspace:
        msg = "No workspace selected. Please specify a workspace with --workspace or run 'tecton workspace select <workspace>'"
        raise click.ClickException(msg)
    return workspace


def _get_scaling_config_str(
    autoscaling_config: Optional[AutoscalingConfig], provisioned_scaling_config: Optional[ProvisionedScalingConfig]
) -> str:
    if autoscaling_config is not None:
        return f"Autoscaling (Min:{autoscaling_config.min_nodes}, Max:{autoscaling_config.max_nodes})"
    elif provisioned_scaling_config:
        return f"Provisioned (Desired:{provisioned_scaling_config.desired_nodes})"
    return ""


def _get_pairs_str(pairs: Dict[str, str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in pairs.items()) if pairs else ""


def _parse_pairs_str(pairs_str: str, var_name: str) -> Dict[str, str]:
    if pairs_str is None:
        return None
    pairs = {}
    for pair in pairs_str.split(","):
        if not pair or pair.count("=") != 1:
            msg = f"Invalid {var_name} format. Expected format: KEY1=VALUE1,KEY2=VALUE2"
            raise click.ClickException(msg)
        k, v = pair.split("=")
        pairs[k] = v
    return pairs


@click.command(
    "feature-server-cache",
    cls=TectonGroup,
    command_category=TectonCommandCategory.INFRA,
    hidden=True,
)
def feature_server_cache():
    """Provision and manage Feature Server Caches."""


def print_feature_server_caches(caches: List[FeatureServerCache]):
    headings = [
        "ID",
        "Workspace",
        "Name",
        "Status",
        "Status Details",
        "Num Shards",
        "Num Replicas",
        "Preferred Maintenance Window",
        "Pending Config",
        "Description",
        "Tags",
        "Created At",
        "Updated At",
    ]
    rows = []
    for cache in caches:
        rows.append(
            (
                cache.id,
                cache.workspace,
                cache.name,
                Status.Name(cache.status),
                cache.status_details or "",
                cache.provisioned_config.num_shards,
                cache.provisioned_config.num_replicas_per_shard,
                cache.preferred_maintenance_window or "",
                cache.pending_config or "",
                cache.metadata.description if cache.HasField("metadata") else "",
                _get_pairs_str(cache.metadata.tags),
                timestamp_to_string(cache.created_at),
                timestamp_to_string(cache.updated_at),
            )
        )
    display_table(headings, rows)


@feature_server_cache.command("create", requires_auth=True, cls=TectonCommand)
@click.option("--name", help="Name of the cache", required=True, type=str)
@click.option("--num-shards", help="Number of shards", required=True, type=int)
@click.option("--num-replicas-per-shard", help="Number of replicas per shard", required=True, type=int)
@click.option(
    "--preferred-maintenance-window",
    help="Preferred maintenance window (format: ddd:hh24:mi-ddd:hh24:mi)",
    required=False,
    type=str,
)
@click.option("--description", help="Description of the cache", required=False, type=str)
@click.option("--tags", help="Tags for the cache", required=False, type=str)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def create_feature_server_cache_cmd(
    name: str,
    num_shards: int,
    num_replicas_per_shard: int,
    preferred_maintenance_window: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    workspace: Optional[str] = None,
):
    """Create a new Feature Server Cache."""
    workspace = _get_validated_workspace(workspace)

    tags = _parse_pairs_str(tags, "tags")

    cache = create_feature_server_cache(
        workspace=workspace,
        name=name,
        num_shards=num_shards,
        num_replicas_per_shard=num_replicas_per_shard,
        preferred_maintenance_window=preferred_maintenance_window,
        description=description,
        tags=tags,
    )

    print_feature_server_caches([cache])


@feature_server_cache.command("get", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the cache", required=True, type=str)
@click_exception_wrapper
def get_feature_server_cache_cmd(id: str):
    """Get a Feature Server Cache by ID."""
    cache = get_feature_server_cache(id=id)

    print_feature_server_caches([cache])


@feature_server_cache.command("list", requires_auth=True, cls=TectonCommand)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def list_feature_server_caches_cmd(workspace: Optional[str] = None):
    """List all Feature Server Caches."""
    workspace = _get_validated_workspace(workspace)

    response = list_feature_server_caches(workspace=workspace)

    print_feature_server_caches(response.caches)


@feature_server_cache.command("update", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the cache", required=True, type=str)
@click.option("--num-shards", help="Number of shards", required=False, type=int)
@click.option("--num-replicas-per-shard", help="Number of replicas per shard", required=False, type=int)
@click.option("--preferred-maintenance-window", help="Preferred maintenance window", required=False, type=str)
@click.option("--description", help="Description of the cache", required=False, type=str)
@click.option("--tags", help="Tags for the cache", required=False, type=str)
@click_exception_wrapper
def update_feature_server_cache_cmd(
    id: str,
    num_shards: Optional[int] = None,
    num_replicas_per_shard: Optional[int] = None,
    preferred_maintenance_window: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
):
    """Update a Feature Server Cache."""
    cache = update_feature_server_cache(
        id=id,
        num_shards=num_shards,
        num_replicas_per_shard=num_replicas_per_shard,
        preferred_maintenance_window=preferred_maintenance_window,
        description=description,
        tags=_parse_pairs_str(tags, "tags"),
    )
    print_feature_server_caches([cache])


@feature_server_cache.command("delete", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the cache", required=True, type=str)
@click_exception_wrapper
def delete_feature_server_cache_cmd(id: str):
    """Delete a Feature Server Cache by ID."""
    delete_feature_server_cache(id=id)
    printer.safe_print(f"Deleted Feature Server Cache with ID {id}")


@click.command(
    "feature-server-group",
    cls=TectonGroup,
    command_category=TectonCommandCategory.INFRA,
    hidden=True,
)
def feature_server_group():
    """Provision and manage Feature Server Groups."""


def print_feature_server_groups(fsgs: List[FeatureServerGroup]):
    headings = [
        "ID",
        "Workspace",
        "Name",
        "Status",
        "Status Details",
        "Scaling",
        "Node Type",
        "Cache ID",
        "Pending Config",
        "Description",
        "Tags",
        "Created At",
        "Updated At",
    ]
    rows = []
    for fsg in fsgs:
        description = ""
        tags = {}
        if fsg.HasField("metadata"):
            description = fsg.metadata.description if fsg.metadata.HasField("description") else ""
            tags = fsg.metadata.tags
        rows.append(
            (
                fsg.id,
                fsg.workspace,
                fsg.name,
                Status.Name(fsg.status),
                fsg.status_details or "",
                _get_scaling_config_str(
                    fsg.autoscaling_config if fsg.HasField("autoscaling_config") else None,
                    fsg.provisioned_config if fsg.HasField("provisioned_config") else None,
                ),
                fsg.node_type,
                fsg.cache_id or "",
                fsg.pending_config or "",
                description,
                _get_pairs_str(tags),
                timestamp_to_string(fsg.created_at),
                timestamp_to_string(fsg.updated_at),
            )
        )
    display_table(headings, rows)


@feature_server_group.command("create", requires_auth=True, cls=TectonCommand)
@click.option("--name", help="Name of the server group", required=True, type=str)
@click.option("--cache-id", help="ID of the Feature Server Cache to use", required=False, type=str)
@click.option("--min-nodes", help="Minimum number of nodes for autoscaling", required=False, type=int)
@click.option("--max-nodes", help="Maximum number of nodes for autoscaling", required=False, type=int)
@click.option("--desired-nodes", help="Fixed number of nodes for provisioned scaling", required=False, type=int)
@click.option("--node-type", help="EC2 instance type", required=False, type=str)
@click.option("--description", help="Description of the server group", required=False, type=str)
@click.option("--tags", help="Tags for the server group", required=False, type=str)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def create_feature_server_group_cmd(
    name: str,
    cache_id: Optional[str] = None,
    min_nodes: Optional[int] = None,
    max_nodes: Optional[int] = None,
    desired_nodes: Optional[int] = None,
    node_type: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    workspace: Optional[str] = None,
):
    """Create a new Feature Server Group."""
    workspace = _get_validated_workspace(workspace)

    server_group = create_feature_server_group(
        workspace=workspace,
        name=name,
        cache_id=cache_id,
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        desired_nodes=desired_nodes,
        node_type=node_type,
        description=description,
        tags=_parse_pairs_str(tags, "tags"),
    )

    print_feature_server_groups([server_group])


@feature_server_group.command("get", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click_exception_wrapper
def get_feature_server_group_cmd(id: str):
    """Get a Feature Server Group by ID."""
    server_group = get_feature_server_group(id=id)

    print_feature_server_groups([server_group])


@feature_server_group.command("list", requires_auth=True, cls=TectonCommand)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def list_feature_server_groups_cmd(workspace: Optional[str] = None):
    """List all Feature Server Groups."""
    workspace = _get_validated_workspace(workspace)

    response = list_feature_server_groups(workspace=workspace)

    print_feature_server_groups(response.feature_server_groups)


@feature_server_group.command("update", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click.option("--min-nodes", help="Minimum number of nodes for autoscaling", required=False, type=int)
@click.option("--max-nodes", help="Maximum number of nodes for autoscaling", required=False, type=int)
@click.option("--desired-nodes", help="Fixed number of nodes for provisioned scaling", required=False, type=int)
@click.option("--node-type", help="EC2 instance type", required=False, type=str)
@click.option("--description", help="Description of the server group", required=False, type=str)
@click.option("--tags", help="Tags to add to the server group", required=False, type=str)
@click_exception_wrapper
def update_feature_server_group_cmd(
    id: str,
    min_nodes: Optional[int] = None,
    max_nodes: Optional[int] = None,
    desired_nodes: Optional[int] = None,
    node_type: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
):
    """Update a Feature Server Group."""
    server_group = update_feature_server_group(
        id=id,
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        desired_nodes=desired_nodes,
        node_type=node_type,
        description=description,
        tags=_parse_pairs_str(tags, "tags"),
    )
    print_feature_server_groups([server_group])


@feature_server_group.command("delete", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click_exception_wrapper
def delete_feature_server_group_cmd(id: str):
    """Delete a Feature Server Group by ID."""
    delete_feature_server_group(id=id)
    printer.safe_print(f"Deleted Feature Server Group with ID {id}")


@click.command(
    "ingest-server-group",
    cls=TectonGroup,
    command_category=TectonCommandCategory.INFRA,
)
def ingest_server_group():
    """Provision and manage Ingest Server Groups."""


def print_ingest_server_groups(isgs: List[IngestServerGroup]):
    headings = [
        "ID",
        "Workspace",
        "Name",
        "Status",
        "Status Details",
        "Scaling",
        "Node Type",
        "Pending Config",
        "Description",
        "Tags",
        "Created At",
        "Updated At",
    ]
    rows = []
    for isg in isgs:
        description = ""
        tags = {}
        if isg.HasField("metadata"):
            description = isg.metadata.description if isg.metadata.HasField("description") else ""
            tags = isg.metadata.tags
        rows.append(
            (
                isg.id,
                isg.workspace,
                isg.name,
                Status.Name(isg.status),
                isg.status_details or "",
                _get_scaling_config_str(
                    isg.autoscaling_config if isg.HasField("autoscaling_config") else None,
                    isg.provisioned_config if isg.HasField("provisioned_config") else None,
                ),
                isg.node_type,
                isg.pending_config or "",
                description,
                _get_pairs_str(tags),
                timestamp_to_string(isg.created_at),
                timestamp_to_string(isg.updated_at),
            )
        )
    display_table(headings, rows)


def _validate_scaling_params(min_nodes: Optional[int], max_nodes: Optional[int], desired_nodes: Optional[int]):
    if (min_nodes is None and max_nodes is None) and desired_nodes is None:
        msg = "Please specify either `min-nodes` and `max-nodes` for autoscaling or `desired-nodes` for provisioned scaling."
        raise click.ClickException(msg)
    if (min_nodes is not None and max_nodes is None) or (min_nodes is None and max_nodes is not None):
        msg = "Both min-nodes and max-nodes must be specified together for autoscaling."
        raise click.ClickException(msg)
    if (min_nodes is not None or max_nodes is not None) and desired_nodes is not None:
        msg = (
            "Either specify min-nodes and max-nodes for autoscaling or desired-nodes for provisioned scaling, not both."
        )
        raise click.ClickException(msg)


@ingest_server_group.command("create", requires_auth=True, cls=TectonCommand)
@click.option("--name", help="Name of the server group", required=True, type=str)
@click.option("--min-nodes", help="Minimum number of nodes for autoscaling", required=False, type=int)
@click.option("--max-nodes", help="Maximum number of nodes for autoscaling", required=False, type=int)
@click.option("--desired-nodes", help="Fixed number of nodes for provisioned scaling", required=False, type=int)
@click.option("--node-type", help="EC2 instance type", required=False, type=str)
@click.option("--description", help="Description of the server group", required=False, type=str)
@click.option("--tags", help="Tags to add to the server group", required=False, type=str)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def create_ingest_server_group_cmd(
    name: str,
    min_nodes: Optional[int] = None,
    max_nodes: Optional[int] = None,
    desired_nodes: Optional[int] = None,
    node_type: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    workspace: Optional[str] = None,
):
    """Create a new Ingest Server Group."""
    workspace = _get_validated_workspace(workspace)

    _validate_scaling_params(min_nodes, max_nodes, desired_nodes)

    server_group = create_ingest_server_group(
        workspace=workspace,
        name=name,
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        desired_nodes=desired_nodes,
        node_type=node_type,
        description=description,
        tags=_parse_pairs_str(tags, "tags"),
    )

    print_ingest_server_groups([server_group])


@ingest_server_group.command("get", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click_exception_wrapper
def get_ingest_server_group_cmd(id: str):
    """Get an Ingest Server Group by ID."""
    server_group = get_ingest_server_group(id=id)

    print_ingest_server_groups([server_group])


@ingest_server_group.command("list", requires_auth=True, cls=TectonCommand)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def list_ingest_server_groups_cmd(workspace: Optional[str] = None):
    """List all Ingest Server Groups."""
    workspace = _get_validated_workspace(workspace)

    response = list_ingest_server_groups(workspace=workspace)
    print_ingest_server_groups(response.ingest_server_groups)


@ingest_server_group.command("update", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click.option("--min-nodes", help="Minimum number of nodes for autoscaling", required=False, type=int)
@click.option("--max-nodes", help="Maximum number of nodes for autoscaling", required=False, type=int)
@click.option("--desired-nodes", help="Fixed number of nodes for provisioned scaling", required=False, type=int)
@click.option("--node-type", help="EC2 instance type", required=False, type=str)
@click.option("--description", help="Description of the server group", required=False, type=str)
@click.option("--tags", help="Tags to add to the server group", required=False, type=str)
@click_exception_wrapper
def update_ingest_server_group_cmd(
    id: str,
    min_nodes: Optional[int] = None,
    max_nodes: Optional[int] = None,
    desired_nodes: Optional[int] = None,
    node_type: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
):
    """Update an Ingest Server Group."""
    server_group = update_ingest_server_group(
        id=id,
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        desired_nodes=desired_nodes,
        node_type=node_type,
        description=description,
        tags=_parse_pairs_str(tags, "tags"),
    )

    print_ingest_server_groups([server_group])


@ingest_server_group.command("delete", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click_exception_wrapper
def delete_ingest_server_group_cmd(id: str):
    """Delete an Ingest Server Group by ID."""
    delete_ingest_server_group(id=id)
    printer.safe_print(f"Deleted Ingest Server Group with ID {id}")


@click.command(
    "transform-server-group",
    cls=TectonGroup,
    command_category=TectonCommandCategory.INFRA,
)
def transform_server_group():
    """Provision and manage Transform Server Groups."""


def print_transform_server_groups(tsgs: List[TransformServerGroup]):
    headings = [
        "ID",
        "Workspace",
        "Name",
        "Status",
        "Status Details",
        "Scaling",
        "Node Type",
        "Environment",
        "Environment Variables",
        "Pending Config",
        "Description",
        "Tags",
        "Created At",
        "Updated At",
    ]
    rows = []
    for ts in tsgs:
        description = ""
        tags = {}
        if ts.HasField("metadata"):
            description = ts.metadata.description if ts.metadata.HasField("description") else ""
            tags = ts.metadata.tags
        rows.append(
            (
                ts.id,
                ts.workspace,
                ts.name,
                Status.Name(ts.status),
                ts.status_details or "",
                _get_scaling_config_str(ts.autoscaling_config, ts.provisioned_config),
                ts.node_type,
                ts.environment,
                _get_pairs_str(ts.environment_variables),
                ts.pending_config or "",
                description,
                _get_pairs_str(tags),
                timestamp_to_string(ts.created_at),
                timestamp_to_string(ts.updated_at),
            )
        )
    display_table(headings, rows)


@transform_server_group.command("create", requires_auth=True, cls=TectonCommand)
@click.option("--name", help="Name of the server group", required=True, type=str)
@click.option("--environment-name", help="Name of the Python environment to use", required=True, type=str)
@click.option("--min-nodes", help="Minimum number of nodes for autoscaling", required=False, type=int)
@click.option("--max-nodes", help="Maximum number of nodes for autoscaling", required=False, type=int)
@click.option("--desired-nodes", help="Fixed number of nodes for provisioned scaling", required=False, type=int)
@click.option("--node-type", help="EC2 instance type", required=False, type=str)
@click.option("--description", help="Description of the server group", required=False, type=str)
@click.option(
    "--tags", help="Tags to add to the server group in the format TAG1=VALUE1,TAG2=VALUE2", required=False, type=str
)
@click.option("--env-vars", help="Environment variable in the format KEY1=VALUE1,KEY2=VALUE2", required=False, type=str)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def create_transform_server_group_cmd(
    name: str,
    environment_name: str,
    min_nodes: Optional[int] = None,
    max_nodes: Optional[int] = None,
    desired_nodes: Optional[int] = None,
    node_type: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    env_vars: Optional[str] = None,
    workspace: Optional[str] = None,
):
    """Create a new Transform Server Group."""
    workspace = _get_validated_workspace(workspace)

    _validate_scaling_params(min_nodes, max_nodes, desired_nodes)

    server_group = create_transform_server_group(
        workspace=workspace,
        name=name,
        environment=environment_name,
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        desired_nodes=desired_nodes,
        node_type=node_type,
        description=description,
        tags=_parse_pairs_str(tags, "tags"),
        environment_variables=_parse_pairs_str(env_vars, "env-vars"),
    )

    print_transform_server_groups([server_group])


@transform_server_group.command("get", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click_exception_wrapper
def get_transform_server_group_cmd(id: str):
    """Get a Transform Server Group by ID."""
    server_group = get_transform_server_group(id=id)

    print_transform_server_groups([server_group])


@transform_server_group.command("list", requires_auth=True, cls=TectonCommand)
@click.option("--workspace", help="Workspace name", required=False, type=str)
@click_exception_wrapper
def list_transform_server_groups_cmd(workspace: Optional[str] = None):
    """List all Transform Server Groups."""
    workspace = _get_validated_workspace(workspace)

    response = list_transform_server_groups(workspace=workspace)

    print_transform_server_groups(response.transform_server_groups)


@transform_server_group.command("update", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click.option("--environment-name", help="Name of the Python environment to use", required=False, type=str)
@click.option("--min-nodes", help="Minimum number of nodes for autoscaling", required=False, type=int)
@click.option("--max-nodes", help="Maximum number of nodes for autoscaling", required=False, type=int)
@click.option("--desired-nodes", help="Fixed number of nodes for provisioned scaling", required=False, type=int)
@click.option("--node-type", help="EC2 instance type", required=False, type=str)
@click.option("--description", help="Description of the server group", required=False, type=str)
@click.option(
    "--tags", help="Tags to add to the server group in the format TAG1=VALUE1,TAG2=VALUE2", required=False, type=str
)
@click.option("--env-vars", help="Environment variable in the format KEY1=VALUE1,KEY2=VALUE2", required=False, type=str)
@click_exception_wrapper
def update_transform_server_group_cmd(
    id: str,
    environment_name: Optional[str] = None,
    min_nodes: Optional[int] = None,
    max_nodes: Optional[int] = None,
    desired_nodes: Optional[int] = None,
    node_type: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    env_vars: Optional[str] = None,
):
    """Update a Transform Server Group."""
    server_group = update_transform_server_group(
        id=id,
        environment=environment_name,
        min_nodes=min_nodes,
        max_nodes=max_nodes,
        desired_nodes=desired_nodes,
        node_type=node_type,
        description=description,
        tags=_parse_pairs_str(tags, "tags"),
        environment_variables=_parse_pairs_str(env_vars, "env-vars"),
    )
    print_transform_server_groups([server_group])


@transform_server_group.command("delete", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the server group", required=True, type=str)
@click_exception_wrapper
def delete_transform_server_group_cmd(id: str):
    """Delete a Transform Server Group by ID."""
    delete_transform_server_group(id=id)
    printer.safe_print(f"Deleted Transform Server Group with ID {id}")


def _display_realtime_logs(response: GetRealtimeLogsResponse):
    display_table(
        headings=["Timestamp", "Node", "Message"],
        display_rows=[(log.timestamp.ToJsonString(), log.node, log.message) for log in response.logs],
        center_align=False,
    )

    if response.warnings:
        printer.safe_print(f"{INFO_SIGN} WARNING: {response.warnings}")


@transform_server_group.command("logs", requires_auth=True, cls=TectonCommand)
@click.option("--id", help="ID of the transform server group", required=True, type=str)
@click.option(
    "-s",
    "--start",
    help="Start timestamp filter, in ISO 8601 format with UTC zone (YYYY-MM-DDThh:mm:ss.SSSSSSZ). Microseconds optional. Defaults to the one day prior to the current time if both start and end time are not specified.",
    required=False,
    type=str,
)
@click.option(
    "-e",
    "--end",
    help="End timestamp filter, in ISO 8601 format with UTC zone (YYYY-MM-DDThh:mm:ss.SSSSSSZ). Microseconds optional. Defaults to the current time if both start and end time are not specified.",
    required=False,
    type=str,
)
@click.option("-t", "--tail", help="Tail number of logs to return (max/default 100)", required=False, type=int)
@click_exception_wrapper
def logs(id: str, start: Optional[str] = None, end: Optional[str] = None, tail: Optional[int] = None):
    server_group_logs = get_realtime_logs(id, start, end, tail)
    _display_realtime_logs(server_group_logs)


# Aliases for the above commands for convenience


@click.command(name="isg", hidden=True, cls=TectonGroup)
def isg():
    """Provision and manage Ingest Server Groups."""


isg.add_command(create_ingest_server_group_cmd)
isg.add_command(get_ingest_server_group_cmd)
isg.add_command(list_ingest_server_groups_cmd)
isg.add_command(update_ingest_server_group_cmd)
isg.add_command(delete_ingest_server_group_cmd)


@click.command(name="tsg", hidden=True, cls=TectonGroup)
def tsg():
    """Provision and manage Transform Server Groups."""


tsg.add_command(create_transform_server_group_cmd)
tsg.add_command(get_transform_server_group_cmd)
tsg.add_command(list_transform_server_groups_cmd)
tsg.add_command(update_transform_server_group_cmd)
tsg.add_command(delete_transform_server_group_cmd)
tsg.add_command(logs)
