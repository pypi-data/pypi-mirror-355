from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    id: Union[None, Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_id: Union[None, Unset, str]
    if isinstance(id, Unset):
        json_id = UNSET
    else:
        json_id = id
    params["id"] = json_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/bodies/",
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
    id: Union[None, Unset, str] = UNSET,
) -> Response[Union[Any, HTTPValidationError]]:
    r"""Bodies

     Abrufen der Körperschaften (Bodies) von der Stadt Bonn OParl API.

    Eine Körperschaft (Body) bildet eine Gebietskörperschaft ab, welche als übergeordnete
    organisatorische Einheit fungiert. Alle anderen Entitäten sind einer Körperschaft zugeordnet.

    Parameter
    ---------
    * **body_id**: ID der spezifischen Körperschaft (optional)
      - Aktuell wird nur \"1\" (Stadt Bonn) unterstützt
      - Ohne Angabe werden alle verfügbaren Körperschaften zurückgegeben

    Rückgabe
    --------
    * **dict**: Körperschafts-Objekt oder Liste von Körperschaften

    Hinweise
    --------
    Die Körperschaft repräsentiert die primäre organisatorische Struktur in OParl,
    typischerweise entsprechend Gemeinderäten oder ähnlichen Regierungsgremien.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-body

    Args:
        id (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
) -> Optional[Union[Any, HTTPValidationError]]:
    r"""Bodies

     Abrufen der Körperschaften (Bodies) von der Stadt Bonn OParl API.

    Eine Körperschaft (Body) bildet eine Gebietskörperschaft ab, welche als übergeordnete
    organisatorische Einheit fungiert. Alle anderen Entitäten sind einer Körperschaft zugeordnet.

    Parameter
    ---------
    * **body_id**: ID der spezifischen Körperschaft (optional)
      - Aktuell wird nur \"1\" (Stadt Bonn) unterstützt
      - Ohne Angabe werden alle verfügbaren Körperschaften zurückgegeben

    Rückgabe
    --------
    * **dict**: Körperschafts-Objekt oder Liste von Körperschaften

    Hinweise
    --------
    Die Körperschaft repräsentiert die primäre organisatorische Struktur in OParl,
    typischerweise entsprechend Gemeinderäten oder ähnlichen Regierungsgremien.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-body

    Args:
        id (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return sync_detailed(
        client=client,
        id=id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
) -> Response[Union[Any, HTTPValidationError]]:
    r"""Bodies

     Abrufen der Körperschaften (Bodies) von der Stadt Bonn OParl API.

    Eine Körperschaft (Body) bildet eine Gebietskörperschaft ab, welche als übergeordnete
    organisatorische Einheit fungiert. Alle anderen Entitäten sind einer Körperschaft zugeordnet.

    Parameter
    ---------
    * **body_id**: ID der spezifischen Körperschaft (optional)
      - Aktuell wird nur \"1\" (Stadt Bonn) unterstützt
      - Ohne Angabe werden alle verfügbaren Körperschaften zurückgegeben

    Rückgabe
    --------
    * **dict**: Körperschafts-Objekt oder Liste von Körperschaften

    Hinweise
    --------
    Die Körperschaft repräsentiert die primäre organisatorische Struktur in OParl,
    typischerweise entsprechend Gemeinderäten oder ähnlichen Regierungsgremien.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-body

    Args:
        id (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    id: Union[None, Unset, str] = UNSET,
) -> Optional[Union[Any, HTTPValidationError]]:
    r"""Bodies

     Abrufen der Körperschaften (Bodies) von der Stadt Bonn OParl API.

    Eine Körperschaft (Body) bildet eine Gebietskörperschaft ab, welche als übergeordnete
    organisatorische Einheit fungiert. Alle anderen Entitäten sind einer Körperschaft zugeordnet.

    Parameter
    ---------
    * **body_id**: ID der spezifischen Körperschaft (optional)
      - Aktuell wird nur \"1\" (Stadt Bonn) unterstützt
      - Ohne Angabe werden alle verfügbaren Körperschaften zurückgegeben

    Rückgabe
    --------
    * **dict**: Körperschafts-Objekt oder Liste von Körperschaften

    Hinweise
    --------
    Die Körperschaft repräsentiert die primäre organisatorische Struktur in OParl,
    typischerweise entsprechend Gemeinderäten oder ähnlichen Regierungsgremien.

    Siehe: https://oparl.org/spezifikation/online-ansicht/#entity-body

    Args:
        id (Union[None, Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            client=client,
            id=id,
        )
    ).parsed
