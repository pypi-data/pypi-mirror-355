from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.paper_list_response import PaperListResponse
from ...models.paper_response import PaperResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, int]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    params["page"] = page

    params["page_size"] = page_size

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/papers/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Union["PaperListResponse", "PaperResponse"]]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union["PaperListResponse", "PaperResponse"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = PaperListResponse.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = PaperResponse.from_dict(data)

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
) -> Response[Union[HTTPValidationError, Union["PaperListResponse", "PaperResponse"]]]:
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
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Response[Union[HTTPValidationError, Union["PaperListResponse", "PaperResponse"]]]:
    """Papers

     Abrufen der Drucksachen (Papers) von der Stadt Bonn OParl API.

    Ein Dokument bildet Drucksachen in der parlamentarischen Arbeit ab. Drucksachen
    repräsentieren Dokumente wie Anträge, Anfragen und Vorlagen, die in der
    parlamentarischen Arbeit bearbeitet werden.

    Parameter
    ---------
    * **paper_id**: ID der spezifischen Drucksache (optional)
      - Bei Angabe: Einzelne Drucksache mit allen Details zurück
      - Ohne Angabe: Paginierte Liste aller Drucksachen zurück
    * **page**: Seitennummer für Paginierung (Standard: 1, Min: 1)
    * **page_size**: Anzahl Elemente pro Seite (Standard: 10, Min: 1, Max: 100)

    Rückgabe
    --------
    * **PaperResponse**: Einzelne Drucksache mit Referenzlinks zu lokalen API-URLs
    * **PaperListResponse**: Paginierte Liste von Drucksachen mit Navigation-Links

    Features
    --------
    * Automatische ChromaDB-Indizierung für abgerufene Drucksachen
    * URL-Umschreibung von Upstream zu lokalen API-Referenzen
    * Paginierung mit konfigurierbarer Seitengröße
    * Navigation-Links (first, prev, next, last) in der Antwort
    * Hintergrundverarbeitung für Performance
    * Umfassende Fehlerbehandlung
    * Logfire-Observability-Integration

    Hinweise
    --------
    Ein Objekt vom Typ oparl:Paper kann eine oder mehrere Dateien (oparl:File)
    enthalten. Weiterhin können Beratungsfolgen (oparl:Consultation) zugeordnet sein.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-paper

    Args:
        id (Union[None, Unset, int]):
        page (Union[Unset, int]): Page number for pagination Default: 1.
        page_size (Union[Unset, int]): Number of items per page Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['PaperListResponse', 'PaperResponse']]]
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
    id: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Optional[Union[HTTPValidationError, Union["PaperListResponse", "PaperResponse"]]]:
    """Papers

     Abrufen der Drucksachen (Papers) von der Stadt Bonn OParl API.

    Ein Dokument bildet Drucksachen in der parlamentarischen Arbeit ab. Drucksachen
    repräsentieren Dokumente wie Anträge, Anfragen und Vorlagen, die in der
    parlamentarischen Arbeit bearbeitet werden.

    Parameter
    ---------
    * **paper_id**: ID der spezifischen Drucksache (optional)
      - Bei Angabe: Einzelne Drucksache mit allen Details zurück
      - Ohne Angabe: Paginierte Liste aller Drucksachen zurück
    * **page**: Seitennummer für Paginierung (Standard: 1, Min: 1)
    * **page_size**: Anzahl Elemente pro Seite (Standard: 10, Min: 1, Max: 100)

    Rückgabe
    --------
    * **PaperResponse**: Einzelne Drucksache mit Referenzlinks zu lokalen API-URLs
    * **PaperListResponse**: Paginierte Liste von Drucksachen mit Navigation-Links

    Features
    --------
    * Automatische ChromaDB-Indizierung für abgerufene Drucksachen
    * URL-Umschreibung von Upstream zu lokalen API-Referenzen
    * Paginierung mit konfigurierbarer Seitengröße
    * Navigation-Links (first, prev, next, last) in der Antwort
    * Hintergrundverarbeitung für Performance
    * Umfassende Fehlerbehandlung
    * Logfire-Observability-Integration

    Hinweise
    --------
    Ein Objekt vom Typ oparl:Paper kann eine oder mehrere Dateien (oparl:File)
    enthalten. Weiterhin können Beratungsfolgen (oparl:Consultation) zugeordnet sein.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-paper

    Args:
        id (Union[None, Unset, int]):
        page (Union[Unset, int]): Page number for pagination Default: 1.
        page_size (Union[Unset, int]): Number of items per page Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['PaperListResponse', 'PaperResponse']]
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
    id: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Response[Union[HTTPValidationError, Union["PaperListResponse", "PaperResponse"]]]:
    """Papers

     Abrufen der Drucksachen (Papers) von der Stadt Bonn OParl API.

    Ein Dokument bildet Drucksachen in der parlamentarischen Arbeit ab. Drucksachen
    repräsentieren Dokumente wie Anträge, Anfragen und Vorlagen, die in der
    parlamentarischen Arbeit bearbeitet werden.

    Parameter
    ---------
    * **paper_id**: ID der spezifischen Drucksache (optional)
      - Bei Angabe: Einzelne Drucksache mit allen Details zurück
      - Ohne Angabe: Paginierte Liste aller Drucksachen zurück
    * **page**: Seitennummer für Paginierung (Standard: 1, Min: 1)
    * **page_size**: Anzahl Elemente pro Seite (Standard: 10, Min: 1, Max: 100)

    Rückgabe
    --------
    * **PaperResponse**: Einzelne Drucksache mit Referenzlinks zu lokalen API-URLs
    * **PaperListResponse**: Paginierte Liste von Drucksachen mit Navigation-Links

    Features
    --------
    * Automatische ChromaDB-Indizierung für abgerufene Drucksachen
    * URL-Umschreibung von Upstream zu lokalen API-Referenzen
    * Paginierung mit konfigurierbarer Seitengröße
    * Navigation-Links (first, prev, next, last) in der Antwort
    * Hintergrundverarbeitung für Performance
    * Umfassende Fehlerbehandlung
    * Logfire-Observability-Integration

    Hinweise
    --------
    Ein Objekt vom Typ oparl:Paper kann eine oder mehrere Dateien (oparl:File)
    enthalten. Weiterhin können Beratungsfolgen (oparl:Consultation) zugeordnet sein.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-paper

    Args:
        id (Union[None, Unset, int]):
        page (Union[Unset, int]): Page number for pagination Default: 1.
        page_size (Union[Unset, int]): Number of items per page Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['PaperListResponse', 'PaperResponse']]]
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
    id: Union[None, Unset, int] = UNSET,
    page: Union[Unset, int] = 1,
    page_size: Union[Unset, int] = 10,
) -> Optional[Union[HTTPValidationError, Union["PaperListResponse", "PaperResponse"]]]:
    """Papers

     Abrufen der Drucksachen (Papers) von der Stadt Bonn OParl API.

    Ein Dokument bildet Drucksachen in der parlamentarischen Arbeit ab. Drucksachen
    repräsentieren Dokumente wie Anträge, Anfragen und Vorlagen, die in der
    parlamentarischen Arbeit bearbeitet werden.

    Parameter
    ---------
    * **paper_id**: ID der spezifischen Drucksache (optional)
      - Bei Angabe: Einzelne Drucksache mit allen Details zurück
      - Ohne Angabe: Paginierte Liste aller Drucksachen zurück
    * **page**: Seitennummer für Paginierung (Standard: 1, Min: 1)
    * **page_size**: Anzahl Elemente pro Seite (Standard: 10, Min: 1, Max: 100)

    Rückgabe
    --------
    * **PaperResponse**: Einzelne Drucksache mit Referenzlinks zu lokalen API-URLs
    * **PaperListResponse**: Paginierte Liste von Drucksachen mit Navigation-Links

    Features
    --------
    * Automatische ChromaDB-Indizierung für abgerufene Drucksachen
    * URL-Umschreibung von Upstream zu lokalen API-Referenzen
    * Paginierung mit konfigurierbarer Seitengröße
    * Navigation-Links (first, prev, next, last) in der Antwort
    * Hintergrundverarbeitung für Performance
    * Umfassende Fehlerbehandlung
    * Logfire-Observability-Integration

    Hinweise
    --------
    Ein Objekt vom Typ oparl:Paper kann eine oder mehrere Dateien (oparl:File)
    enthalten. Weiterhin können Beratungsfolgen (oparl:Consultation) zugeordnet sein.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-paper

    Args:
        id (Union[None, Unset, int]):
        page (Union[Unset, int]): Page number for pagination Default: 1.
        page_size (Union[Unset, int]): Number of items per page Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['PaperListResponse', 'PaperResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            page=page,
            page_size=page_size,
        )
    ).parsed
