"""The endpoints for oauth_token objects.

SPDX-License-Identifier: AGPL-3.0-only OR BSD-3-Clause-Clear
"""

import os
import typing as t

import cg_request_args as rqa
from cg_maybe import Maybe, Nothing

from .. import parsers, utils

if t.TYPE_CHECKING or os.getenv("CG_EAGERIMPORT", False):
    from .. import client
    from ..models.oauth_token import OAuthToken
    from ..models.post_oauth_token_data import PostOAuthTokenData
    from ..models.setup_oauth_result import SetupOAuthResult


_ClientT = t.TypeVar("_ClientT", bound="client._BaseClient")


class OAuthTokenService(t.Generic[_ClientT]):
    __slots__ = ("__client",)

    def __init__(self, client: _ClientT) -> None:
        self.__client = client

    def get_all(
        self: "OAuthTokenService[client.AuthenticatedClient]",
        *,
        extra_parameters: t.Optional[
            t.Mapping[str, t.Union[str, bool, int, float]]
        ] = None,
    ) -> "t.Sequence[OAuthToken]":
        """Get all OAuth tokens of the current user.

        :param extra_parameters: The extra query parameters you might want to
            add. By default no extra query parameters are added.

        :returns: The token.
        """

        url = "/api/v1/oauth_tokens/"
        params = extra_parameters or {}

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.oauth_token import OAuthToken

            return parsers.JsonResponseParser(
                rqa.List(parsers.ParserFor.make(OAuthToken))
            ).try_parse(resp)

        from ..models.any_error import AnyError

        raise utils.get_error(
            resp,
            (
                (
                    (400, 409, 401, 403, 404, 429, 500),
                    utils.unpack_union(AnyError),
                ),
            ),
        )

    def post(
        self: "OAuthTokenService[client.AuthenticatedClient]",
        json_body: t.Union[dict, list, "PostOAuthTokenData"],
        *,
        extra_parameters: t.Optional[
            t.Mapping[str, t.Union[str, bool, int, float]]
        ] = None,
    ) -> "SetupOAuthResult":
        """Create an OAuth token for the specified provider.

        :param json_body: The body of the request. See
            :class:`.PostOAuthTokenData` for information about the possible
            fields. You can provide this data as a :class:`.PostOAuthTokenData`
            or as a dictionary.
        :param extra_parameters: The extra query parameters you might want to
            add. By default no extra query parameters are added.

        :returns: The OAuth callback URL.
        """

        url = "/api/v1/oauth_tokens/"
        params = extra_parameters or {}

        with self.__client as client:
            resp = client.http.post(
                url=url, json=utils.to_dict(json_body), params=params
            )
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.setup_oauth_result import SetupOAuthResult

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(SetupOAuthResult)
            ).try_parse(resp)

        from ..models.any_error import AnyError

        raise utils.get_error(
            resp,
            (
                (
                    (400, 409, 401, 403, 404, 429, 500),
                    utils.unpack_union(AnyError),
                ),
            ),
        )

    def get(
        self: "OAuthTokenService[client.AuthenticatedClient]",
        *,
        token_id: "str",
        is_temp_id: "bool" = False,
        extra_parameters: t.Optional[
            t.Mapping[str, t.Union[str, bool, int, float]]
        ] = None,
    ) -> "OAuthToken":
        """Get an OAuth token by id.

        :param token_id: The id of the token to get.
        :param is_temp_id: Whether the id in the request is a `temp_id` or an
            `id`.
        :param extra_parameters: The extra query parameters you might want to
            add. By default no extra query parameters are added.

        :returns: The requested token.
        """

        url = "/api/v1/oauth_tokens/{tokenId}".format(tokenId=token_id)
        params: t.Dict[str, t.Any] = {
            **(extra_parameters or {}),
            "is_temp_id": utils.to_dict(is_temp_id),
        }

        with self.__client as client:
            resp = client.http.get(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 200):
            from ..models.oauth_token import OAuthToken

            return parsers.JsonResponseParser(
                parsers.ParserFor.make(OAuthToken)
            ).try_parse(resp)

        from ..models.any_error import AnyError

        raise utils.get_error(
            resp,
            (
                (
                    (400, 409, 401, 403, 404, 429, 500),
                    utils.unpack_union(AnyError),
                ),
            ),
        )

    def delete(
        self: "OAuthTokenService[client.AuthenticatedClient]",
        *,
        token_id: "str",
        extra_parameters: t.Optional[
            t.Mapping[str, t.Union[str, bool, int, float]]
        ] = None,
    ) -> "None":
        """Delete an OAuth token.

        :param token_id: The id of the token you want to delete.
        :param extra_parameters: The extra query parameters you might want to
            add. By default no extra query parameters are added.

        :returns: Nothing.
        """

        url = "/api/v1/oauth_tokens/{tokenId}".format(tokenId=token_id)
        params = extra_parameters or {}

        with self.__client as client:
            resp = client.http.delete(url=url, params=params)
        utils.log_warnings(resp)

        if utils.response_code_matches(resp.status_code, 204):
            return parsers.ConstantlyParser(None).try_parse(resp)

        from ..models.any_error import AnyError

        raise utils.get_error(
            resp,
            (
                (
                    (400, 409, 401, 403, 404, 429, 500),
                    utils.unpack_union(AnyError),
                ),
            ),
        )
