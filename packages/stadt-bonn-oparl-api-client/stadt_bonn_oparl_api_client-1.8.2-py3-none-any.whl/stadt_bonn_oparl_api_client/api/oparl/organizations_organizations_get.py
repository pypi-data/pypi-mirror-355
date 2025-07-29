from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.organization_list_response import OrganizationListResponse
from ...models.organization_response import OrganizationResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, str]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    json_body: Union[None, Unset, str]
    if isinstance(body, Unset):
        json_body = UNSET
    else:
        json_body = body
    params["body"] = json_body

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/organizations/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Union["OrganizationListResponse", "OrganizationResponse"]]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union["OrganizationListResponse", "OrganizationResponse"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = OrganizationResponse.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = OrganizationListResponse.from_dict(data)

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
) -> Response[Union[HTTPValidationError, Union["OrganizationListResponse", "OrganizationResponse"]]]:
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
    body: Union[None, Unset, str] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["OrganizationListResponse", "OrganizationResponse"]]]:
    """Organizations

     Abrufen der Organisationen (Organizations) von der Stadt Bonn OParl API.

    Organisationen dienen dazu, Gruppierungen von Personen abzubilden, die in der
    parlamentarischen Arbeit eine Rolle spielen. Dazu zählen insbesondere Fraktionen
    und Gremien. Unterstützt umfassende Filterung, Paginierung und automatisches
    ChromaDB-Caching für verbesserte Performance.

    Parameter
    ---------
    * **organization_id**: ID der spezifischen OParl Organisation, also der id parameter der id_ref!!
    (optional)
      - Gibt eine einzelne Organisation zurück
      - Kann nicht zusammen mit body_id verwendet werden
    * **body_id**: ID der Körperschaft für Organisationsfilterung (optional)
      - Gibt alle Organisationen dieser Körperschaft zurück
      - Kann nicht zusammen mit organization_id verwendet werden
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **OrganizationResponse | OrganizationListResponse**: Einzelne Organisation oder paginierte Liste
    mit
      Metadaten und Navigationslinks

    Fehlerbehandlung
    ---------------
    * **400**: organization_id und body_id gleichzeitig angegeben
    * **400**: Ungültiges Format für organization_id (muss eine positiver Integer sein)
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    In der Praxis zählen zu den Organisationen insbesondere Fraktionen und Gremien.
    Alle Ergebnisse werden automatisch in ChromaDB für erweiterte Suchfähigkeiten
    zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-organization

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        page (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['OrganizationListResponse', 'OrganizationResponse']]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
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
    body: Union[None, Unset, str] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["OrganizationListResponse", "OrganizationResponse"]]]:
    """Organizations

     Abrufen der Organisationen (Organizations) von der Stadt Bonn OParl API.

    Organisationen dienen dazu, Gruppierungen von Personen abzubilden, die in der
    parlamentarischen Arbeit eine Rolle spielen. Dazu zählen insbesondere Fraktionen
    und Gremien. Unterstützt umfassende Filterung, Paginierung und automatisches
    ChromaDB-Caching für verbesserte Performance.

    Parameter
    ---------
    * **organization_id**: ID der spezifischen OParl Organisation, also der id parameter der id_ref!!
    (optional)
      - Gibt eine einzelne Organisation zurück
      - Kann nicht zusammen mit body_id verwendet werden
    * **body_id**: ID der Körperschaft für Organisationsfilterung (optional)
      - Gibt alle Organisationen dieser Körperschaft zurück
      - Kann nicht zusammen mit organization_id verwendet werden
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **OrganizationResponse | OrganizationListResponse**: Einzelne Organisation oder paginierte Liste
    mit
      Metadaten und Navigationslinks

    Fehlerbehandlung
    ---------------
    * **400**: organization_id und body_id gleichzeitig angegeben
    * **400**: Ungültiges Format für organization_id (muss eine positiver Integer sein)
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    In der Praxis zählen zu den Organisationen insbesondere Fraktionen und Gremien.
    Alle Ergebnisse werden automatisch in ChromaDB für erweiterte Suchfähigkeiten
    zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-organization

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        page (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['OrganizationListResponse', 'OrganizationResponse']]
    """

    return sync_detailed(
        client=client,
        id=id,
        body=body,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["OrganizationListResponse", "OrganizationResponse"]]]:
    """Organizations

     Abrufen der Organisationen (Organizations) von der Stadt Bonn OParl API.

    Organisationen dienen dazu, Gruppierungen von Personen abzubilden, die in der
    parlamentarischen Arbeit eine Rolle spielen. Dazu zählen insbesondere Fraktionen
    und Gremien. Unterstützt umfassende Filterung, Paginierung und automatisches
    ChromaDB-Caching für verbesserte Performance.

    Parameter
    ---------
    * **organization_id**: ID der spezifischen OParl Organisation, also der id parameter der id_ref!!
    (optional)
      - Gibt eine einzelne Organisation zurück
      - Kann nicht zusammen mit body_id verwendet werden
    * **body_id**: ID der Körperschaft für Organisationsfilterung (optional)
      - Gibt alle Organisationen dieser Körperschaft zurück
      - Kann nicht zusammen mit organization_id verwendet werden
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **OrganizationResponse | OrganizationListResponse**: Einzelne Organisation oder paginierte Liste
    mit
      Metadaten und Navigationslinks

    Fehlerbehandlung
    ---------------
    * **400**: organization_id und body_id gleichzeitig angegeben
    * **400**: Ungültiges Format für organization_id (muss eine positiver Integer sein)
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    In der Praxis zählen zu den Organisationen insbesondere Fraktionen und Gremien.
    Alle Ergebnisse werden automatisch in ChromaDB für erweiterte Suchfähigkeiten
    zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-organization

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        page (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['OrganizationListResponse', 'OrganizationResponse']]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        page=page,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, str] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["OrganizationListResponse", "OrganizationResponse"]]]:
    """Organizations

     Abrufen der Organisationen (Organizations) von der Stadt Bonn OParl API.

    Organisationen dienen dazu, Gruppierungen von Personen abzubilden, die in der
    parlamentarischen Arbeit eine Rolle spielen. Dazu zählen insbesondere Fraktionen
    und Gremien. Unterstützt umfassende Filterung, Paginierung und automatisches
    ChromaDB-Caching für verbesserte Performance.

    Parameter
    ---------
    * **organization_id**: ID der spezifischen OParl Organisation, also der id parameter der id_ref!!
    (optional)
      - Gibt eine einzelne Organisation zurück
      - Kann nicht zusammen mit body_id verwendet werden
    * **body_id**: ID der Körperschaft für Organisationsfilterung (optional)
      - Gibt alle Organisationen dieser Körperschaft zurück
      - Kann nicht zusammen mit organization_id verwendet werden
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **OrganizationResponse | OrganizationListResponse**: Einzelne Organisation oder paginierte Liste
    mit
      Metadaten und Navigationslinks

    Fehlerbehandlung
    ---------------
    * **400**: organization_id und body_id gleichzeitig angegeben
    * **400**: Ungültiges Format für organization_id (muss eine positiver Integer sein)
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    In der Praxis zählen zu den Organisationen insbesondere Fraktionen und Gremien.
    Alle Ergebnisse werden automatisch in ChromaDB für erweiterte Suchfähigkeiten
    zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-organization

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, str]):
        page (Union[Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['OrganizationListResponse', 'OrganizationResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            body=body,
            page=page,
            page_size=page_size,
        )
    ).parsed
