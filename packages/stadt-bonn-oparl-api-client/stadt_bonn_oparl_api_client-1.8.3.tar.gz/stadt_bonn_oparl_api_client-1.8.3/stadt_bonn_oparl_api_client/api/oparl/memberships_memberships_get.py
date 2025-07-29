from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.membership_list_response import MembershipListResponse
from ...models.membership_response import MembershipResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, int] = UNSET,
    person: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, int]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    json_person: Union[None, Unset, int]
    if isinstance(person, Unset):
        json_person = UNSET
    else:
        json_person = person
    params["person"] = json_person

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
        "url": "/memberships/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[HTTPValidationError, Union["MembershipListResponse", "MembershipResponse"]]]:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Union["MembershipListResponse", "MembershipResponse"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = MembershipResponse.from_dict(data)

                return response_200_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = MembershipListResponse.from_dict(data)

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
) -> Response[Union[HTTPValidationError, Union["MembershipListResponse", "MembershipResponse"]]]:
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
    person: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["MembershipListResponse", "MembershipResponse"]]]:
    """Memberships

     Abrufen der Mitgliedschaften (Memberships) von der Stadt Bonn OParl API.

    Mitgliedschaften dienen dazu, die Zugehörigkeit von Personen zu Gruppierungen
    darzustellen. Diese können zeitlich begrenzt sein und bestimmte Rollen oder
    Positionen innerhalb der Gruppierung abbilden.

    Parameter
    ---------
    * **membership_id**: ID der spezifischen Mitgliedschaft (optional)
      - Gibt eine einzelne Mitgliedschaft zurück
      - Kann nicht zusammen mit person_id oder body_id verwendet werden
    * **person_id**: ID der Person für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften dieser Person zurück
    * **body_id**: ID der Körperschaft für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften innerhalb dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **MembershipResponse | MembershipListResponse**: Einzelne Mitgliedschaft oder Liste von
    Mitgliedschaften

    Fehlerbehandlung
    ---------------
    * **400**: membership_id zusammen mit person_id oder body_id angegeben
    * **400**: Keiner der id-Parameter wurde angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Mitgliedschaften können abbilden, dass eine Person eine bestimmte Rolle bzw.
    Position innerhalb der Gruppierung innehat (z.B. Fraktionsvorsitz).
    Alle Ergebnisse werden automatisch in ChromaDB zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-membership

    Args:
        id (Union[None, Unset, int]):
        person (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['MembershipListResponse', 'MembershipResponse']]]
    """

    kwargs = _get_kwargs(
        id=id,
        person=person,
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
    id: Union[None, Unset, int] = UNSET,
    person: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["MembershipListResponse", "MembershipResponse"]]]:
    """Memberships

     Abrufen der Mitgliedschaften (Memberships) von der Stadt Bonn OParl API.

    Mitgliedschaften dienen dazu, die Zugehörigkeit von Personen zu Gruppierungen
    darzustellen. Diese können zeitlich begrenzt sein und bestimmte Rollen oder
    Positionen innerhalb der Gruppierung abbilden.

    Parameter
    ---------
    * **membership_id**: ID der spezifischen Mitgliedschaft (optional)
      - Gibt eine einzelne Mitgliedschaft zurück
      - Kann nicht zusammen mit person_id oder body_id verwendet werden
    * **person_id**: ID der Person für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften dieser Person zurück
    * **body_id**: ID der Körperschaft für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften innerhalb dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **MembershipResponse | MembershipListResponse**: Einzelne Mitgliedschaft oder Liste von
    Mitgliedschaften

    Fehlerbehandlung
    ---------------
    * **400**: membership_id zusammen mit person_id oder body_id angegeben
    * **400**: Keiner der id-Parameter wurde angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Mitgliedschaften können abbilden, dass eine Person eine bestimmte Rolle bzw.
    Position innerhalb der Gruppierung innehat (z.B. Fraktionsvorsitz).
    Alle Ergebnisse werden automatisch in ChromaDB zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-membership

    Args:
        id (Union[None, Unset, int]):
        person (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['MembershipListResponse', 'MembershipResponse']]
    """

    return sync_detailed(
        client=client,
        id=id,
        person=person,
        body=body,
        page=page,
        page_size=page_size,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    person: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Response[Union[HTTPValidationError, Union["MembershipListResponse", "MembershipResponse"]]]:
    """Memberships

     Abrufen der Mitgliedschaften (Memberships) von der Stadt Bonn OParl API.

    Mitgliedschaften dienen dazu, die Zugehörigkeit von Personen zu Gruppierungen
    darzustellen. Diese können zeitlich begrenzt sein und bestimmte Rollen oder
    Positionen innerhalb der Gruppierung abbilden.

    Parameter
    ---------
    * **membership_id**: ID der spezifischen Mitgliedschaft (optional)
      - Gibt eine einzelne Mitgliedschaft zurück
      - Kann nicht zusammen mit person_id oder body_id verwendet werden
    * **person_id**: ID der Person für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften dieser Person zurück
    * **body_id**: ID der Körperschaft für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften innerhalb dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **MembershipResponse | MembershipListResponse**: Einzelne Mitgliedschaft oder Liste von
    Mitgliedschaften

    Fehlerbehandlung
    ---------------
    * **400**: membership_id zusammen mit person_id oder body_id angegeben
    * **400**: Keiner der id-Parameter wurde angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Mitgliedschaften können abbilden, dass eine Person eine bestimmte Rolle bzw.
    Position innerhalb der Gruppierung innehat (z.B. Fraktionsvorsitz).
    Alle Ergebnisse werden automatisch in ChromaDB zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-membership

    Args:
        id (Union[None, Unset, int]):
        person (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['MembershipListResponse', 'MembershipResponse']]]
    """

    kwargs = _get_kwargs(
        id=id,
        person=person,
        body=body,
        page=page,
        page_size=page_size,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, int] = UNSET,
    person: Union[None, Unset, int] = UNSET,
    body: Union[None, Unset, int] = UNSET,
    page: Union[None, Unset, int] = 1,
    page_size: Union[Unset, int] = 5,
) -> Optional[Union[HTTPValidationError, Union["MembershipListResponse", "MembershipResponse"]]]:
    """Memberships

     Abrufen der Mitgliedschaften (Memberships) von der Stadt Bonn OParl API.

    Mitgliedschaften dienen dazu, die Zugehörigkeit von Personen zu Gruppierungen
    darzustellen. Diese können zeitlich begrenzt sein und bestimmte Rollen oder
    Positionen innerhalb der Gruppierung abbilden.

    Parameter
    ---------
    * **membership_id**: ID der spezifischen Mitgliedschaft (optional)
      - Gibt eine einzelne Mitgliedschaft zurück
      - Kann nicht zusammen mit person_id oder body_id verwendet werden
    * **person_id**: ID der Person für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften dieser Person zurück
    * **body_id**: ID der Körperschaft für Mitgliedschaftsabruf (optional)
      - Gibt alle Mitgliedschaften innerhalb dieser Körperschaft zurück
    * **page**: Seitennummer für Paginierung (1-1000, Standard: 1)
    * **page_size**: Anzahl Elemente pro Seite (1-100, Standard: 5)

    Rückgabe
    --------
    * **MembershipResponse | MembershipListResponse**: Einzelne Mitgliedschaft oder Liste von
    Mitgliedschaften

    Fehlerbehandlung
    ---------------
    * **400**: membership_id zusammen mit person_id oder body_id angegeben
    * **400**: Keiner der id-Parameter wurde angegeben
    * **500**: OParl API-Anfrage fehlgeschlagen

    Hinweise
    --------
    Mitgliedschaften können abbilden, dass eine Person eine bestimmte Rolle bzw.
    Position innerhalb der Gruppierung innehat (z.B. Fraktionsvorsitz).
    Alle Ergebnisse werden automatisch in ChromaDB zwischengespeichert.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-membership

    Args:
        id (Union[None, Unset, int]):
        person (Union[None, Unset, int]):
        body (Union[None, Unset, int]):
        page (Union[None, Unset, int]):  Default: 1.
        page_size (Union[Unset, int]):  Default: 5.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['MembershipListResponse', 'MembershipResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
            person=person,
            body=body,
            page=page,
            page_size=page_size,
        )
    ).parsed
