from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.location_response import LocationResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, str]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    json_page: Union[None, Unset, int]
    if isinstance(page, Unset):
        json_page = UNSET
    else:
        json_page = page
    params["page"] = json_page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/locations/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, LocationResponse]]:
    if response.status_code == 200:
        response_200 = LocationResponse.from_dict(response.json())

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
) -> Response[Union[HTTPValidationError, LocationResponse]]:
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
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, LocationResponse]]:
    """Locations

     Abrufen der Orte (Locations) von der Stadt Bonn OParl API.

    Ortsangaben (Locations) dienen dazu, einen Ortsbezug formal abzubilden.
    Sie können sowohl aus Textinformationen (Straßennamen, Adressen) als auch
    aus Geodaten bestehen.

    Parameter
    ---------
    * **location_id**: ID des spezifischen Ortes (erforderlich)
      - Dieser Parameter ist obligatorisch
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Aktuell nicht verwendet
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Aktuell nicht verwendet

    Rückgabe
    --------
    * **LocationResponse**: Orts-Objekt mit räumlichen Referenzinformationen

    Fehlerbehandlung
    ---------------
    * **400**: location_id nicht angegeben
    * **404**: Ort als gelöscht markiert oder nicht gefunden
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Ortsangaben sind nicht auf einzelne Positionen beschränkt, sondern können
    eine Vielzahl von Positionen, Flächen, Strecken etc. abdecken.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-location

    Args:
        id (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, LocationResponse]]
    """

    kwargs = _get_kwargs(
        id=id,
        page=page,
        page_size=page_size,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, LocationResponse]]:
    """Locations

     Abrufen der Orte (Locations) von der Stadt Bonn OParl API.

    Ortsangaben (Locations) dienen dazu, einen Ortsbezug formal abzubilden.
    Sie können sowohl aus Textinformationen (Straßennamen, Adressen) als auch
    aus Geodaten bestehen.

    Parameter
    ---------
    * **location_id**: ID des spezifischen Ortes (erforderlich)
      - Dieser Parameter ist obligatorisch
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Aktuell nicht verwendet
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Aktuell nicht verwendet

    Rückgabe
    --------
    * **LocationResponse**: Orts-Objekt mit räumlichen Referenzinformationen

    Fehlerbehandlung
    ---------------
    * **400**: location_id nicht angegeben
    * **404**: Ort als gelöscht markiert oder nicht gefunden
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Ortsangaben sind nicht auf einzelne Positionen beschränkt, sondern können
    eine Vielzahl von Positionen, Flächen, Strecken etc. abdecken.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-location

    Args:
        id (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, LocationResponse]
    """

    return sync_detailed(
        client=client,
        id=id,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, LocationResponse]]:
    """Locations

     Abrufen der Orte (Locations) von der Stadt Bonn OParl API.

    Ortsangaben (Locations) dienen dazu, einen Ortsbezug formal abzubilden.
    Sie können sowohl aus Textinformationen (Straßennamen, Adressen) als auch
    aus Geodaten bestehen.

    Parameter
    ---------
    * **location_id**: ID des spezifischen Ortes (erforderlich)
      - Dieser Parameter ist obligatorisch
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Aktuell nicht verwendet
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Aktuell nicht verwendet

    Rückgabe
    --------
    * **LocationResponse**: Orts-Objekt mit räumlichen Referenzinformationen

    Fehlerbehandlung
    ---------------
    * **400**: location_id nicht angegeben
    * **404**: Ort als gelöscht markiert oder nicht gefunden
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Ortsangaben sind nicht auf einzelne Positionen beschränkt, sondern können
    eine Vielzahl von Positionen, Flächen, Strecken etc. abdecken.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-location

    Args:
        id (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, LocationResponse]]
    """

    kwargs = _get_kwargs(
        id=id,
        page=page,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, LocationResponse]]:
    """Locations

     Abrufen der Orte (Locations) von der Stadt Bonn OParl API.

    Ortsangaben (Locations) dienen dazu, einen Ortsbezug formal abzubilden.
    Sie können sowohl aus Textinformationen (Straßennamen, Adressen) als auch
    aus Geodaten bestehen.

    Parameter
    ---------
    * **location_id**: ID des spezifischen Ortes (erforderlich)
      - Dieser Parameter ist obligatorisch
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
      - Aktuell nicht verwendet
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)
      - Aktuell nicht verwendet

    Rückgabe
    --------
    * **LocationResponse**: Orts-Objekt mit räumlichen Referenzinformationen

    Fehlerbehandlung
    ---------------
    * **400**: location_id nicht angegeben
    * **404**: Ort als gelöscht markiert oder nicht gefunden
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Ortsangaben sind nicht auf einzelne Positionen beschränkt, sondern können
    eine Vielzahl von Positionen, Flächen, Strecken etc. abdecken.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-location

    Args:
        id (Union[None, Unset, str]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, LocationResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            page=page,
            page_size=page_size,
        )
    ).parsed
