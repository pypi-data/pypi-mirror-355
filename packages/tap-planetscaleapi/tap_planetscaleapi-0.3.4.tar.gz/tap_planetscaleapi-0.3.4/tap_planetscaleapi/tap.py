"""PlanetScaleAPI tap class."""

from __future__ import annotations

import typing as t

import requests
from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers
from toolz.dicttoolz import get_in

from tap_planetscaleapi import streams

OPENAPI_URL = "https://api.planetscale.com/v1/openapi-spec"
STREAMS = [
    streams.OrganizationsStream,
    streams.OrganizationRegionsStream,
    streams.DatabasesStream,
    streams.DatabaseReadOnlyRegionsStream,
    streams.DatabaseRegionsStream,
    streams.BranchesStream,
    # streams.BranchSchemaStream,
    streams.BackupsStream,
    streams.PasswordsStream,
    streams.DeployRequestsStream,
    streams.DeployOperationsStream,
    streams.DeployRequestReviewsStreams,
    # streams.OAuthApplicationsStream,
    streams.RegionsStream,
]

if t.TYPE_CHECKING:
    from tap_planetscaleapi.client import PlanetScaleAPIStream


class TapPlanetScaleAPI(Tap):
    """PlanetScaleAPI tap class."""

    name = "tap-planetscaleapi"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "service_token_id",
            th.StringType,
            required=True,
            description="The service token ID, visible on the service token page",
        ),
        th.Property(
            "service_token",
            th.StringType,
            required=True,
            secret=True,
            description="The service token value",
        ),
    ).to_dict()

    def get_openapi_schema(self) -> dict[t.Any, t.Any]:
        """Retrieve OpenAPI schema for this API.

        Returns:
            OpenAPI schema.
        """
        return requests.get(OPENAPI_URL, timeout=5).json()  # type: ignore[no-any-return]

    def discover_streams(self) -> list[PlanetScaleAPIStream]:
        """Return a list of discovered streams.

        Returns:
            A list of Neon Serverless Postgres streams.
        """
        streams: list[PlanetScaleAPIStream] = []
        openapi_schema = self.get_openapi_schema()

        for stream_type in STREAMS:
            schema = get_in(stream_type.schema_path, openapi_schema)
            streams.append(stream_type(tap=self, schema=schema))

        return sorted(streams, key=lambda x: x.name)


if __name__ == "__main__":
    TapPlanetScaleAPI.cli()
