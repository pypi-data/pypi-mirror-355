from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.consultation import Consultation
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, int] = UNSET,
    bi: Union[None, Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, int]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    json_bi: Union[None, Unset, int]
    if isinstance(bi, Unset):
        json_bi = UNSET
    else:
        json_bi = bi
    params["bi"] = json_bi

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/consultations/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[Consultation, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = Consultation.from_dict(response.json())

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
) -> Response[Union[Consultation, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    bi: Union[None, Unset, int] = UNSET,
) -> Response[Union[Consultation, HTTPValidationError]]:
    """Consultations

     Abrufen der Konsultationen von der Stadt Bonn OParl API.

    Konsultationen sind öffentliche Anhörungen oder Konsultationen zu
    bestimmten Themen, die von der Stadt Bonn durchgeführt werden. Sie bildet die Beratung einer
    Drucksache
    in einer Sitzung ab. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit
    stattgefunden hat
    oder diese für die Zukunft geplant ist.

    Parameter
    ---------
    * consultation_id: Optional[int]
        - ID der Konsultation, um eine spezifische Konsultation abzurufen.
    * bi: Optional[int]
        - Bi-Nummer der Konsultation, um eine spezifische Konsultation abzurufen.

    Args:
        id (Union[None, Unset, int]):
        bi (Union[None, Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Consultation, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        id=id,
        bi=bi,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    bi: Union[None, Unset, int] = UNSET,
) -> Optional[Union[Consultation, HTTPValidationError]]:
    """Consultations

     Abrufen der Konsultationen von der Stadt Bonn OParl API.

    Konsultationen sind öffentliche Anhörungen oder Konsultationen zu
    bestimmten Themen, die von der Stadt Bonn durchgeführt werden. Sie bildet die Beratung einer
    Drucksache
    in einer Sitzung ab. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit
    stattgefunden hat
    oder diese für die Zukunft geplant ist.

    Parameter
    ---------
    * consultation_id: Optional[int]
        - ID der Konsultation, um eine spezifische Konsultation abzurufen.
    * bi: Optional[int]
        - Bi-Nummer der Konsultation, um eine spezifische Konsultation abzurufen.

    Args:
        id (Union[None, Unset, int]):
        bi (Union[None, Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Consultation, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        id=id,
        bi=bi,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    bi: Union[None, Unset, int] = UNSET,
) -> Response[Union[Consultation, HTTPValidationError]]:
    """Consultations

     Abrufen der Konsultationen von der Stadt Bonn OParl API.

    Konsultationen sind öffentliche Anhörungen oder Konsultationen zu
    bestimmten Themen, die von der Stadt Bonn durchgeführt werden. Sie bildet die Beratung einer
    Drucksache
    in einer Sitzung ab. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit
    stattgefunden hat
    oder diese für die Zukunft geplant ist.

    Parameter
    ---------
    * consultation_id: Optional[int]
        - ID der Konsultation, um eine spezifische Konsultation abzurufen.
    * bi: Optional[int]
        - Bi-Nummer der Konsultation, um eine spezifische Konsultation abzurufen.

    Args:
        id (Union[None, Unset, int]):
        bi (Union[None, Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Consultation, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        id=id,
        bi=bi,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    bi: Union[None, Unset, int] = UNSET,
) -> Optional[Union[Consultation, HTTPValidationError]]:
    """Consultations

     Abrufen der Konsultationen von der Stadt Bonn OParl API.

    Konsultationen sind öffentliche Anhörungen oder Konsultationen zu
    bestimmten Themen, die von der Stadt Bonn durchgeführt werden. Sie bildet die Beratung einer
    Drucksache
    in einer Sitzung ab. Dabei ist es nicht entscheidend, ob diese Beratung in der Vergangenheit
    stattgefunden hat
    oder diese für die Zukunft geplant ist.

    Parameter
    ---------
    * consultation_id: Optional[int]
        - ID der Konsultation, um eine spezifische Konsultation abzurufen.
    * bi: Optional[int]
        - Bi-Nummer der Konsultation, um eine spezifische Konsultation abzurufen.

    Args:
        id (Union[None, Unset, int]):
        bi (Union[None, Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Consultation, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            bi=bi,
        )
    ).parsed
