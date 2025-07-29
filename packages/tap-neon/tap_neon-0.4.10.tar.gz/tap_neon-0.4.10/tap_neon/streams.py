"""Stream type classes for tap-neon."""

from __future__ import annotations

import typing as t

from tap_neon.client import NeonStream

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context, Record


__all__ = [
    "Branches",
    "Databases",
    "Endpoints",
    "Operations",
    "Projects",
    "Roles",
]


class Projects(NeonStream):
    """Projects stream."""

    name = "projects"
    path = "/projects"
    primary_keys = ("id",)
    replication_key = None
    swagger_ref = "ProjectListItem"
    records_jsonpath = "$.projects[*]"

    def get_child_context(
        self,
        record: Record,
        context: Context | None,  # noqa: ARG002
    ) -> dict[str, t.Any]:
        """Return the child context for this record.

        Args:
            record: The record to get the child context for.
            context: The parent context.

        Returns:
            The child context.
        """
        return {"project_id": record["id"]}

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Initialize the projects stream."""
        super().__init__(*args, **kwargs)
        self._schema["properties"]["default_endpoint_settings"]["properties"][
            "autoscaling_limit_min_cu"
        ]["minimum"] = 0
        self._schema["properties"]["default_endpoint_settings"]["properties"][
            "autoscaling_limit_max_cu"
        ]["minimum"] = 0


class Operations(NeonStream):
    """Operations stream."""

    name = "operations"
    path = "/projects/{project_id}/operations"
    primary_keys = ("id",)
    replication_key = None
    swagger_ref = "Operation"
    records_jsonpath = "$.operations[*]"
    next_page_token_jsonpath = "$.pagination.cursor"  # noqa: S105
    parent_stream_type = Projects


class Branches(NeonStream):
    """Branches stream."""

    name = "branches"
    path = "/projects/{project_id}/branches"
    primary_keys = ("id",)
    replication_key = None
    swagger_ref = "Branch"
    records_jsonpath = "$.branches[*]"
    parent_stream_type = Projects

    def get_child_context(
        self,
        record: Record,
        context: Context | None,  # noqa: ARG002
    ) -> dict[str, t.Any]:
        """Add branch_id to context.

        Args:
            record: A record dict.
            context: A context dict.

        Returns:
            The updated context dict.
        """
        return {
            "project_id": record["project_id"],
            "branch_id": record["id"],
        }


class Databases(NeonStream):
    """Databases stream."""

    name = "databases"
    path = "/projects/{project_id}/branches/{branch_id}/databases"
    primary_keys = ("id",)
    replication_key = None
    swagger_ref = "Database"
    records_jsonpath = "$.databases[*]"
    parent_stream_type = Branches


class Roles(NeonStream):
    """Roles stream."""

    name = "roles"
    path = "/projects/{project_id}/branches/{branch_id}/roles"
    primary_keys = ("name",)
    replication_key = None
    swagger_ref = "Role"
    records_jsonpath = "$.roles[*]"
    parent_stream_type = Branches


class Endpoints(NeonStream):
    """Endpoints stream."""

    name = "endpoints"
    path = "/projects/{project_id}/endpoints"
    primary_keys = ("id",)
    replication_key = None
    swagger_ref = "Endpoint"
    records_jsonpath = "$.endpoints[*]"
    parent_stream_type = Projects

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Initialize the endpoints stream."""
        super().__init__(*args, **kwargs)
        self._schema["properties"]["pooler_mode"]["enum"].append("")
