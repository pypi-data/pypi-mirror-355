from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.meeting_list_response import MeetingListResponse
from ...models.meeting_response import MeetingResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    organization: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    limit: Union[Unset, int] = 5,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, int]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    json_body: Union[None, Unset, int]
    if isinstance(body, Unset):
        json_body = UNSET
    else:
        json_body = body
    params["body"] = json_body

    json_organization: Union[None, Unset, int]
    if isinstance(organization, Unset):
        json_organization = UNSET
    else:
        json_organization = organization
    params["organization"] = json_organization

    params["page"] = page

    params["limit"] = limit

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/meetings/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Union["MeetingListResponse", "MeetingResponse"]]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union["MeetingListResponse", "MeetingResponse"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = MeetingResponse.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = MeetingListResponse.from_dict(data)

            return response_200_type_1

        response_200 = _parse_response_200(response.json())

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
) -> Response[Union[HTTPValidationError, Union["MeetingListResponse", "MeetingResponse"]]]:
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
    body: Union[None, Unset, int] = UNSET,
    organization: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    limit: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["MeetingListResponse", "MeetingResponse"]]]:
    """Meetings

     Abrufen der Sitzungen (Meetings) von der Stadt Bonn OParl API.

    Eine Sitzung ist die Versammlung einer oder mehrerer Gruppierungen zu einem
    bestimmten Zeitpunkt an einem bestimmten Ort. Sitzungen enthalten geladene
    Teilnehmer, Tagesordnungspunkte und zugehörige Dokumente.

    Parameter
    ---------
    * **meeting_id**: ID der spezifischen Sitzung (optional)
      - Gibt eine einzelne Sitzung zurück
      - Kann nicht zusammen mit body_id oder organization_id verwendet werden
    * **body_id**: ID der Körperschaft für Sitzungsabruf (optional)
      - Noch nicht implementiert
    * **organization_id**: ID der Organisation für Sitzungsabruf (optional)
      - Gibt Sitzungen dieser Organisation zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Noch nicht implementiert
    * **limit**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Noch nicht implementiert

    Rückgabe
    --------
    * **MeetingResponse | MeetingListResponse**: Einzelne Sitzung oder Liste von Sitzungen

    Fehlerbehandlung
    ---------------
    * **400**: Mehrere Filterparameter gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen
    * **501**: Nicht unterstützte Parameterkombinationen

    Hinweise
    --------
    Die geladenen Teilnehmer sind als oparl:Person-Objekte referenziert.
    Verschiedene Dateien (Einladung, Ergebnis- und Wortprotokoll, Anlagen)
    können referenziert werden. Inhalte werden durch oparl:AgendaItem abgebildet.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-meeting

    Args:
        id (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        organization (Union[None, Unset, int]):
        page (Union[Unset, int]):  Default: 1.
        limit (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['MeetingListResponse', 'MeetingResponse']]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        organization=organization,
        page=page,
        limit=limit,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    organization: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    limit: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["MeetingListResponse", "MeetingResponse"]]]:
    """Meetings

     Abrufen der Sitzungen (Meetings) von der Stadt Bonn OParl API.

    Eine Sitzung ist die Versammlung einer oder mehrerer Gruppierungen zu einem
    bestimmten Zeitpunkt an einem bestimmten Ort. Sitzungen enthalten geladene
    Teilnehmer, Tagesordnungspunkte und zugehörige Dokumente.

    Parameter
    ---------
    * **meeting_id**: ID der spezifischen Sitzung (optional)
      - Gibt eine einzelne Sitzung zurück
      - Kann nicht zusammen mit body_id oder organization_id verwendet werden
    * **body_id**: ID der Körperschaft für Sitzungsabruf (optional)
      - Noch nicht implementiert
    * **organization_id**: ID der Organisation für Sitzungsabruf (optional)
      - Gibt Sitzungen dieser Organisation zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Noch nicht implementiert
    * **limit**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Noch nicht implementiert

    Rückgabe
    --------
    * **MeetingResponse | MeetingListResponse**: Einzelne Sitzung oder Liste von Sitzungen

    Fehlerbehandlung
    ---------------
    * **400**: Mehrere Filterparameter gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen
    * **501**: Nicht unterstützte Parameterkombinationen

    Hinweise
    --------
    Die geladenen Teilnehmer sind als oparl:Person-Objekte referenziert.
    Verschiedene Dateien (Einladung, Ergebnis- und Wortprotokoll, Anlagen)
    können referenziert werden. Inhalte werden durch oparl:AgendaItem abgebildet.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-meeting

    Args:
        id (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        organization (Union[None, Unset, int]):
        page (Union[Unset, int]):  Default: 1.
        limit (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['MeetingListResponse', 'MeetingResponse']]
    """

    return sync_detailed(
        client=client,
        id=id,
        body=body,
        organization=organization,
        page=page,
        limit=limit,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    organization: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    limit: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["MeetingListResponse", "MeetingResponse"]]]:
    """Meetings

     Abrufen der Sitzungen (Meetings) von der Stadt Bonn OParl API.

    Eine Sitzung ist die Versammlung einer oder mehrerer Gruppierungen zu einem
    bestimmten Zeitpunkt an einem bestimmten Ort. Sitzungen enthalten geladene
    Teilnehmer, Tagesordnungspunkte und zugehörige Dokumente.

    Parameter
    ---------
    * **meeting_id**: ID der spezifischen Sitzung (optional)
      - Gibt eine einzelne Sitzung zurück
      - Kann nicht zusammen mit body_id oder organization_id verwendet werden
    * **body_id**: ID der Körperschaft für Sitzungsabruf (optional)
      - Noch nicht implementiert
    * **organization_id**: ID der Organisation für Sitzungsabruf (optional)
      - Gibt Sitzungen dieser Organisation zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Noch nicht implementiert
    * **limit**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Noch nicht implementiert

    Rückgabe
    --------
    * **MeetingResponse | MeetingListResponse**: Einzelne Sitzung oder Liste von Sitzungen

    Fehlerbehandlung
    ---------------
    * **400**: Mehrere Filterparameter gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen
    * **501**: Nicht unterstützte Parameterkombinationen

    Hinweise
    --------
    Die geladenen Teilnehmer sind als oparl:Person-Objekte referenziert.
    Verschiedene Dateien (Einladung, Ergebnis- und Wortprotokoll, Anlagen)
    können referenziert werden. Inhalte werden durch oparl:AgendaItem abgebildet.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-meeting

    Args:
        id (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        organization (Union[None, Unset, int]):
        page (Union[Unset, int]):  Default: 1.
        limit (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['MeetingListResponse', 'MeetingResponse']]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        organization=organization,
        page=page,
        limit=limit,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    organization: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    limit: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["MeetingListResponse", "MeetingResponse"]]]:
    """Meetings

     Abrufen der Sitzungen (Meetings) von der Stadt Bonn OParl API.

    Eine Sitzung ist die Versammlung einer oder mehrerer Gruppierungen zu einem
    bestimmten Zeitpunkt an einem bestimmten Ort. Sitzungen enthalten geladene
    Teilnehmer, Tagesordnungspunkte und zugehörige Dokumente.

    Parameter
    ---------
    * **meeting_id**: ID der spezifischen Sitzung (optional)
      - Gibt eine einzelne Sitzung zurück
      - Kann nicht zusammen mit body_id oder organization_id verwendet werden
    * **body_id**: ID der Körperschaft für Sitzungsabruf (optional)
      - Noch nicht implementiert
    * **organization_id**: ID der Organisation für Sitzungsabruf (optional)
      - Gibt Sitzungen dieser Organisation zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Noch nicht implementiert
    * **limit**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Noch nicht implementiert

    Rückgabe
    --------
    * **MeetingResponse | MeetingListResponse**: Einzelne Sitzung oder Liste von Sitzungen

    Fehlerbehandlung
    ---------------
    * **400**: Mehrere Filterparameter gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen
    * **501**: Nicht unterstützte Parameterkombinationen

    Hinweise
    --------
    Die geladenen Teilnehmer sind als oparl:Person-Objekte referenziert.
    Verschiedene Dateien (Einladung, Ergebnis- und Wortprotokoll, Anlagen)
    können referenziert werden. Inhalte werden durch oparl:AgendaItem abgebildet.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-meeting

    Args:
        id (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        organization (Union[None, Unset, int]):
        page (Union[Unset, int]):  Default: 1.
        limit (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['MeetingListResponse', 'MeetingResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            body=body,
            organization=organization,
            page=page,
            limit=limit,
        )
    ).parsed
