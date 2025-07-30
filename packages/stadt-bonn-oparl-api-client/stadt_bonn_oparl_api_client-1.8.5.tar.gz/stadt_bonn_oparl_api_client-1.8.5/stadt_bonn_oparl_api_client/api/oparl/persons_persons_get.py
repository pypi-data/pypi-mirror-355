from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.person_list_response import PersonListResponse
from ...models.person_response import PersonResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, str] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = UNSET,
    page_size: Union[Unset, int] = 5,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, str]
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
        "url": "/persons/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Union["PersonListResponse", "PersonResponse"]]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union["PersonListResponse", "PersonResponse"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = PersonResponse.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = PersonListResponse.from_dict(data)

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
) -> Response[Union[HTTPValidationError, Union["PersonListResponse", "PersonResponse"]]]:
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
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = UNSET,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["PersonListResponse", "PersonResponse"]]]:
    """Persons

     Abrufen der Personen (Persons) von der Stadt Bonn OParl API.

    Jede natürliche Person, die in der parlamentarischen Arbeit tätig und insbesondere
    Mitglied in einer Gruppierung ist, wird als Person abgebildet. Alle Personen
    werden automatisch in ChromaDB für verbesserte Suche zwischengespeichert.

    Parameter
    ---------
    * **person_id**: ID der spezifischen Person (optional)
      - Gibt eine einzelne Person zurück
    * **body_id**: ID der Körperschaft für Personenfilterung (optional)
      - Gibt Personen dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, optional)
      - Nur mit body_id Parameter verwendet

    Rückgabe
    --------
    * **PersonResponse | PersonListResponse**: Einzelne Person oder paginierte Liste von Personen

    Fehlerbehandlung
    ---------------
    * **400**: person_id und body_id gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Repräsentiert natürliche Personen, die in der parlamentarischen Arbeit aktiv sind,
    insbesondere Mitglieder von Organisationen (oparl:Organization) gemäß
    OParl-Spezifikation.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-person

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['PersonListResponse', 'PersonResponse']]]
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
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = UNSET,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["PersonListResponse", "PersonResponse"]]]:
    """Persons

     Abrufen der Personen (Persons) von der Stadt Bonn OParl API.

    Jede natürliche Person, die in der parlamentarischen Arbeit tätig und insbesondere
    Mitglied in einer Gruppierung ist, wird als Person abgebildet. Alle Personen
    werden automatisch in ChromaDB für verbesserte Suche zwischengespeichert.

    Parameter
    ---------
    * **person_id**: ID der spezifischen Person (optional)
      - Gibt eine einzelne Person zurück
    * **body_id**: ID der Körperschaft für Personenfilterung (optional)
      - Gibt Personen dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, optional)
      - Nur mit body_id Parameter verwendet

    Rückgabe
    --------
    * **PersonResponse | PersonListResponse**: Einzelne Person oder paginierte Liste von Personen

    Fehlerbehandlung
    ---------------
    * **400**: person_id und body_id gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Repräsentiert natürliche Personen, die in der parlamentarischen Arbeit aktiv sind,
    insbesondere Mitglieder von Organisationen (oparl:Organization) gemäß
    OParl-Spezifikation.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-person

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['PersonListResponse', 'PersonResponse']]
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
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = UNSET,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["PersonListResponse", "PersonResponse"]]]:
    """Persons

     Abrufen der Personen (Persons) von der Stadt Bonn OParl API.

    Jede natürliche Person, die in der parlamentarischen Arbeit tätig und insbesondere
    Mitglied in einer Gruppierung ist, wird als Person abgebildet. Alle Personen
    werden automatisch in ChromaDB für verbesserte Suche zwischengespeichert.

    Parameter
    ---------
    * **person_id**: ID der spezifischen Person (optional)
      - Gibt eine einzelne Person zurück
    * **body_id**: ID der Körperschaft für Personenfilterung (optional)
      - Gibt Personen dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, optional)
      - Nur mit body_id Parameter verwendet

    Rückgabe
    --------
    * **PersonResponse | PersonListResponse**: Einzelne Person oder paginierte Liste von Personen

    Fehlerbehandlung
    ---------------
    * **400**: person_id und body_id gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Repräsentiert natürliche Personen, die in der parlamentarischen Arbeit aktiv sind,
    insbesondere Mitglieder von Organisationen (oparl:Organization) gemäß
    OParl-Spezifikation.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-person

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['PersonListResponse', 'PersonResponse']]]
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
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = UNSET,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["PersonListResponse", "PersonResponse"]]]:
    """Persons

     Abrufen der Personen (Persons) von der Stadt Bonn OParl API.

    Jede natürliche Person, die in der parlamentarischen Arbeit tätig und insbesondere
    Mitglied in einer Gruppierung ist, wird als Person abgebildet. Alle Personen
    werden automatisch in ChromaDB für verbesserte Suche zwischengespeichert.

    Parameter
    ---------
    * **person_id**: ID der spezifischen Person (optional)
      - Gibt eine einzelne Person zurück
    * **body_id**: ID der Körperschaft für Personenfilterung (optional)
      - Gibt Personen dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, optional)
      - Nur mit body_id Parameter verwendet

    Rückgabe
    --------
    * **PersonResponse | PersonListResponse**: Einzelne Person oder paginierte Liste von Personen

    Fehlerbehandlung
    ---------------
    * **400**: person_id und body_id gleichzeitig angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Repräsentiert natürliche Personen, die in der parlamentarischen Arbeit aktiv sind,
    insbesondere Mitglieder von Organisationen (oparl:Organization) gemäß
    OParl-Spezifikation.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-person

    Args:
        id (Union[None, Unset, str]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['PersonListResponse', 'PersonResponse']]
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
