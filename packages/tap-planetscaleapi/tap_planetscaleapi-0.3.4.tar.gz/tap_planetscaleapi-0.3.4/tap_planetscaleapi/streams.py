"""Stream type classes for tap-planetscaleapi."""

from __future__ import annotations

import functools
import typing as t

from tap_planetscaleapi.client import PlanetScaleAPIStream

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context


class OrganizationsStream(PlanetScaleAPIStream):
    """Organizations."""

    name = "organizations"
    path = "/v1/organizations"
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )

    def get_child_context(self, record: dict, context: Context | None) -> dict | None:  # noqa: ARG002
        """Return a dictionary of child context.

        Args:
            record: A record object.
            context: The current context.

        Returns:
            A dictionary of child context.
        """
        return {
            "organization_id": record["id"],
            "organization_name": record["name"],
        }

    def post_process(self, row: dict, context: Context | None = None) -> dict | None:  # noqa: D102, ARG002
        row["invoice_budget_amount"] = float(row["invoice_budget_amount"])
        return row


class OrganizationRegionsStream(PlanetScaleAPIStream):
    """Organization regions."""

    parent_stream_type = OrganizationsStream

    name = "organization_regions"
    path = "/v1/organizations/{organization_name}/regions"
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{name}/regions",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class DatabasesStream(PlanetScaleAPIStream):
    """Databases."""

    parent_stream_type = OrganizationsStream

    name = "databases"
    path = "/v1/organizations/{organization_name}/databases"
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )

    def get_child_context(self, record: dict, context: Context | None) -> dict | None:
        """Return a dictionary of child context.

        Args:
            record: A record object.
            context: The current context.

        Returns:
            A dictionary of child context.
        """
        return {
            "database_id": record["id"],
            "database_name": record["name"],
            "organization_id": context["organization_id"] if context else None,
            "organization_name": context["organization_name"] if context else None,
        }


class DatabaseReadOnlyRegionsStream(PlanetScaleAPIStream):
    """Database read-only regions."""

    parent_stream_type = DatabasesStream

    name = "database_read_only_regions"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/read-only-regions"  # noqa: E501
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{name}/read-only-regions",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class DatabaseRegionsStream(PlanetScaleAPIStream):
    """Database regions."""

    parent_stream_type = DatabasesStream

    name = "database_regions"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/regions"
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{name}/regions",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class BranchesStream(PlanetScaleAPIStream):
    """Branches."""

    parent_stream_type = DatabasesStream

    name = "branches"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/branches"
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{database}/branches",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )

    def get_child_context(self, record: dict, context: Context | None) -> dict | None:
        """Return a dictionary of child context.

        Args:
            record: A record object.
            context: The current context.

        Returns:
            A dictionary of child context.
        """
        return {
            "branch_id": record["id"],
            "branch_name": record["name"],
            "database_id": context["database_id"] if context else None,
            "database_name": context["database_name"] if context else None,
            "organization_id": context["organization_id"] if context else None,
            "organization_name": context["organization_name"] if context else None,
        }


class BranchSchemaStream(PlanetScaleAPIStream):
    """Branch schema."""

    parent_stream_type = BranchesStream

    name = "branch_schema"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/branches/{branch_name}/schema"  # noqa: E501
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{database}/branches/{name}/schema",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class BackupsStream(PlanetScaleAPIStream):
    """Backups."""

    parent_stream_type = BranchesStream

    name = "backups"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/branches/{branch_name}/backups"  # noqa: E501
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{database}/branches/{branch}/backups",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class PasswordsStream(PlanetScaleAPIStream):
    """Passwords."""

    parent_stream_type = BranchesStream

    name = "passwords"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/branches/{branch_name}/passwords"  # noqa: E501
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{database}/branches/{branch}/passwords",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )

    @functools.cached_property
    def schema(self) -> dict[str, t.Any]:
        """Patch the stream schema."""
        schema = super().schema
        schema["properties"]["cidrs"]["type"] = ["array", "null"]
        return schema


class DeployRequestsStream(PlanetScaleAPIStream):
    """Deploy requests."""

    parent_stream_type = BranchesStream

    name = "deploy_requests"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/deploy-requests"  # noqa: E501
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{database}/deploy-requests",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )

    def get_child_context(self, record: dict, context: Context | None) -> dict | None:
        """Return a dictionary of child context.

        Args:
            record: A record object.
            context: The current context.

        Returns:
            A dictionary of child context.
        """
        return {
            "deploy_request_id": record["id"],
            "deploy_request_number": record["number"],
            "branch_id": context["branch_id"] if context else None,
            "branch_name": context["branch_name"] if context else None,
            "database_id": context["database_id"] if context else None,
            "database_name": context["database_name"] if context else None,
            "organization_id": context["organization_id"] if context else None,
            "organization_name": context["organization_name"] if context else None,
        }


class DeployOperationsStream(PlanetScaleAPIStream):
    """Deploy operations."""

    parent_stream_type = DeployRequestsStream

    name = "deploy_operations"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/deploy-requests/{deploy_request_number}/operations"  # noqa: E501
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{database}/deploy-requests/{number}/operations",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class DeployRequestReviewsStreams(PlanetScaleAPIStream):
    """Deploy request reviews."""

    parent_stream_type = DeployRequestsStream

    name = "deploy_request_reviews"
    path = "/v1/organizations/{organization_name}/databases/{database_name}/deploy-requests/{deploy_request_number}/reviews"  # noqa: E501
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/databases/{database}/deploy-requests/{number}/reviews",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class OAuthApplicationsStream(PlanetScaleAPIStream):
    """OAuth applications."""

    parent_stream_type = OrganizationsStream

    name = "oauth_applications"
    path = "/v1/organizations/{organization_id}/oauth-applications"
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/organizations/{organization}/oauth-applications",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )


class RegionsStream(PlanetScaleAPIStream):
    """Regions."""

    name = "regions"
    path = "/v1/regions"
    primary_keys = ("id",)
    replication_key = None
    schema_path = (
        "paths",
        "/regions",
        "get",
        "responses",
        "200",
        "schema",
        "properties",
        "data",
        "items",
    )
