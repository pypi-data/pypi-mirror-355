from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.agenda_item_response import AgendaItemResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, str] = UNSET,
    meeting: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    organization: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, str]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    json_meeting: Union[None, Unset, str]
    if isinstance(meeting, Unset):
        json_meeting = UNSET
    else:
        json_meeting = meeting
    params["meeting"] = json_meeting

    json_body: Union[None, Unset, str]
    if isinstance(body, Unset):
        json_body = UNSET
    else:
        json_body = body
    params["body"] = json_body

    json_organization: Union[None, Unset, str]
    if isinstance(organization, Unset):
        json_organization = UNSET
    else:
        json_organization = organization
    params["organization"] = json_organization

    json_page: Union[None, Unset, int]
    if isinstance(page, Unset):
        json_page = UNSET
    else:
        json_page = page
    params["page"] = json_page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/agendaitems/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[AgendaItemResponse, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = AgendaItemResponse.from_dict(response.json())

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
) -> Response[Union[AgendaItemResponse, HTTPValidationError]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    meeting: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    organization: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Response[Union[AgendaItemResponse, HTTPValidationError]]:
    """Agenda Items

     Abrufen der Tagesordnungspunkte (AgendaItems) von der Stadt Bonn OParl API.

    Ein Tagesordnungspunkt ist ein Gegenstand der Beratung in einer Sitzung.
    Jeder Tagesordnungspunkt gehört zu genau einer Sitzung und kann verschiedene
    Objekte und Personen zugeordnet haben.

    Parameter
    ---------
    * **agenda_item_id**: ID des spezifischen Tagesordnungspunktes (optional)
    * **meeting_id**: ID der Sitzung für Tagesordnungsabruf (optional)
    * **body_id**: ID der Körperschaft für Tagesordnungsabruf (optional)
    * **organization_id**: ID der Organisation für Tagesordnungsabruf (optional)

    Rückgabe
    --------
    * **AgendaItemResponse**: Spezifischer Tagesordnungspunkt mit allen Details

    Hinweise
    --------
    Verschiedene Objekte können einem Tagesordnungspunkt zugeordnet sein,
    vor allem Objekte vom Typ oparl:Consultation (Beratungsgegenstände).
    Außerdem können Personen zugeordnet sein, die eine bestimmte Rolle
    beim Tagesordnungspunkt wahrnehmen.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-agendaitem

    Args:
        id (Union[None, Unset, str]):
        meeting (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        organization (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AgendaItemResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        id=id,
        meeting=meeting,
        body=body,
        organization=organization,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    meeting: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    organization: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Optional[Union[AgendaItemResponse, HTTPValidationError]]:
    """Agenda Items

     Abrufen der Tagesordnungspunkte (AgendaItems) von der Stadt Bonn OParl API.

    Ein Tagesordnungspunkt ist ein Gegenstand der Beratung in einer Sitzung.
    Jeder Tagesordnungspunkt gehört zu genau einer Sitzung und kann verschiedene
    Objekte und Personen zugeordnet haben.

    Parameter
    ---------
    * **agenda_item_id**: ID des spezifischen Tagesordnungspunktes (optional)
    * **meeting_id**: ID der Sitzung für Tagesordnungsabruf (optional)
    * **body_id**: ID der Körperschaft für Tagesordnungsabruf (optional)
    * **organization_id**: ID der Organisation für Tagesordnungsabruf (optional)

    Rückgabe
    --------
    * **AgendaItemResponse**: Spezifischer Tagesordnungspunkt mit allen Details

    Hinweise
    --------
    Verschiedene Objekte können einem Tagesordnungspunkt zugeordnet sein,
    vor allem Objekte vom Typ oparl:Consultation (Beratungsgegenstände).
    Außerdem können Personen zugeordnet sein, die eine bestimmte Rolle
    beim Tagesordnungspunkt wahrnehmen.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-agendaitem

    Args:
        id (Union[None, Unset, str]):
        meeting (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        organization (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AgendaItemResponse, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        id=id,
        meeting=meeting,
        body=body,
        organization=organization,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    meeting: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    organization: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Response[Union[AgendaItemResponse, HTTPValidationError]]:
    """Agenda Items

     Abrufen der Tagesordnungspunkte (AgendaItems) von der Stadt Bonn OParl API.

    Ein Tagesordnungspunkt ist ein Gegenstand der Beratung in einer Sitzung.
    Jeder Tagesordnungspunkt gehört zu genau einer Sitzung und kann verschiedene
    Objekte und Personen zugeordnet haben.

    Parameter
    ---------
    * **agenda_item_id**: ID des spezifischen Tagesordnungspunktes (optional)
    * **meeting_id**: ID der Sitzung für Tagesordnungsabruf (optional)
    * **body_id**: ID der Körperschaft für Tagesordnungsabruf (optional)
    * **organization_id**: ID der Organisation für Tagesordnungsabruf (optional)

    Rückgabe
    --------
    * **AgendaItemResponse**: Spezifischer Tagesordnungspunkt mit allen Details

    Hinweise
    --------
    Verschiedene Objekte können einem Tagesordnungspunkt zugeordnet sein,
    vor allem Objekte vom Typ oparl:Consultation (Beratungsgegenstände).
    Außerdem können Personen zugeordnet sein, die eine bestimmte Rolle
    beim Tagesordnungspunkt wahrnehmen.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-agendaitem

    Args:
        id (Union[None, Unset, str]):
        meeting (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        organization (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AgendaItemResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        id=id,
        meeting=meeting,
        body=body,
        organization=organization,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    meeting: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    organization: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
) -> Optional[Union[AgendaItemResponse, HTTPValidationError]]:
    """Agenda Items

     Abrufen der Tagesordnungspunkte (AgendaItems) von der Stadt Bonn OParl API.

    Ein Tagesordnungspunkt ist ein Gegenstand der Beratung in einer Sitzung.
    Jeder Tagesordnungspunkt gehört zu genau einer Sitzung und kann verschiedene
    Objekte und Personen zugeordnet haben.

    Parameter
    ---------
    * **agenda_item_id**: ID des spezifischen Tagesordnungspunktes (optional)
    * **meeting_id**: ID der Sitzung für Tagesordnungsabruf (optional)
    * **body_id**: ID der Körperschaft für Tagesordnungsabruf (optional)
    * **organization_id**: ID der Organisation für Tagesordnungsabruf (optional)

    Rückgabe
    --------
    * **AgendaItemResponse**: Spezifischer Tagesordnungspunkt mit allen Details

    Hinweise
    --------
    Verschiedene Objekte können einem Tagesordnungspunkt zugeordnet sein,
    vor allem Objekte vom Typ oparl:Consultation (Beratungsgegenstände).
    Außerdem können Personen zugeordnet sein, die eine bestimmte Rolle
    beim Tagesordnungspunkt wahrnehmen.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-agendaitem

    Args:
        id (Union[None, Unset, str]):
        meeting (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        organization (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AgendaItemResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            meeting=meeting,
            body=body,
            organization=organization,
            page=page,
        )
    ).parsed
