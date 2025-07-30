"""REST client handling, including PlanetScaleAPIStream base class."""

from __future__ import annotations

import typing as t

import requests
from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.pagination import BasePageNumberPaginator
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context

_Auth = t.Callable[[requests.PreparedRequest], requests.PreparedRequest]


class PlanetScaleAPIStream(RESTStream[int]):
    """PlanetScaleAPI stream class."""

    # Abstract class properties:
    schema_path: tuple[str, ...]

    # Class properties
    PAGE_SIZE = 100
    records_jsonpath = "$.data[*]"

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return "https://api.planetscale.com"

    @property
    def authenticator(self) -> APIKeyAuthenticator:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        token_id = self.config["service_token_id"]
        token = self.config["service_token"]
        return APIKeyAuthenticator.create_for_stream(
            self,
            key="Authorization",
            value=f"{token_id}:{token}",
            location="header",
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        return {
            "accept": "application/json",
        }

    def get_new_paginator(self) -> BasePageNumberPaginator:
        """Create a new pagination helper instance.

        Returns:
            A pagination helper instance.
        """
        return BasePageNumberPaginator(1)

    def get_url_params(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ANN401
    ) -> dict[str, t.Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The stream context.
            next_page_token: The next page index or value.

        Returns:
            A dictionary of URL query parameters.
        """
        params: dict[str, t.Any] = {"per_page": self.PAGE_SIZE}
        if next_page_token:
            params["page"] = next_page_token

        return params
