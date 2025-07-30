from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    query: str,
    entity_type: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["query"] = query

    json_entity_type: Union[None, Unset, str]
    if isinstance(entity_type, Unset):
        json_entity_type = UNSET
    else:
        json_entity_type = entity_type
    params["entity_type"] = json_entity_type

    json_page: Union[None, Unset, int]
    if isinstance(page, Unset):
        json_page = UNSET
    else:
        json_page = page
    params["page"] = json_page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/search",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = response.json()
        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[Any, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    query: str,
    entity_type: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Response[Union[Any, HTTPValidationError]]:
    """Search

     Search for entities in the Stadt Bonn OParl API.

    **This endpoint is not implemented yet!**

    Args:
        query (str): Search query for entities
        entity_type (Union[None, Unset, str]): Type of entity to search for (e.g., person,
            organization)
        page (Union[None, Unset, int]): Page number for results Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        query=query,
        entity_type=entity_type,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    query: str,
    entity_type: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Search

     Search for entities in the Stadt Bonn OParl API.

    **This endpoint is not implemented yet!**

    Args:
        query (str): Search query for entities
        entity_type (Union[None, Unset, str]): Type of entity to search for (e.g., person,
            organization)
        page (Union[None, Unset, int]): Page number for results Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        query=query,
        entity_type=entity_type,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    query: str,
    entity_type: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Response[Union[Any, HTTPValidationError]]:
    """Search

     Search for entities in the Stadt Bonn OParl API.

    **This endpoint is not implemented yet!**

    Args:
        query (str): Search query for entities
        entity_type (Union[None, Unset, str]): Type of entity to search for (e.g., person,
            organization)
        page (Union[None, Unset, int]): Page number for results Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        query=query,
        entity_type=entity_type,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    query: str,
    entity_type: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Search

     Search for entities in the Stadt Bonn OParl API.

    **This endpoint is not implemented yet!**

    Args:
        query (str): Search query for entities
        entity_type (Union[None, Unset, str]): Type of entity to search for (e.g., person,
            organization)
        page (Union[None, Unset, int]): Page number for results Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            query=query,
            entity_type=entity_type,
            page=page,
        )
    ).parsed
