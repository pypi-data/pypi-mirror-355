import asyncio
import http
from concurrent.futures import ThreadPoolExecutor
from json import JSONDecodeError
from typing import Any, Optional

from aiohttp import ClientError, ClientResponse, ClientSession
from loguru import logger

from citycom_mv_api.const import ERROR_RESPONSE_DESCRIPTOR_DESCRIPTION_FIELD, ERROR_RESPONSE_DESCRIPTOR_FIELD
from citycom_mv_api.models.exceptions import CitycomError, LoginError


def add_auth_bearer_to_headers(headers: dict[str, str], token: str) -> dict[str, str]:
    """
    Add JWT bearer token to the Authorization header.
    Args:
    headers (dict): The headers dictionary to be modified.
    token (str): The JWT token to be added to the headers.
    Returns:
    dict: The modified headers dictionary with the JWT token added.
    """
    headers["Authorization"] = f"Bearer {token}"
    return headers

def parse_error_response(resp: ClientResponse, json_resp: dict[str, Any]):
    """
    A function to parse error responses from
    """
    logger.warning(f"Failed call: (Code {resp.status}): {resp.reason}")
    if len(json_resp) > 0:
        error_type = json_resp.get(ERROR_RESPONSE_DESCRIPTOR_FIELD)
        error_descriptor = json_resp.get(ERROR_RESPONSE_DESCRIPTOR_DESCRIPTION_FIELD)
        if error_type is not None and error_descriptor is not None:
            raise LoginError(resp.status, error_type + ": "
                              + error_descriptor)
        elif error_descriptor is not None:
            raise CitycomError(resp.status, error_descriptor)
    raise CitycomError(resp.status, resp.reason)


async def send_get_request(
    session: ClientSession, url: str, timeout: Optional[int] = 60, headers: Optional[dict] = None
) -> dict[str, Any]:
    try:
        if not headers:
            headers = session.headers

        if not timeout:
            timeout = session.timeout

        logger.debug(f"HTTP GET: {url}")
        resp = await session.get(url=url, headers=headers, timeout=timeout)
        json_resp: dict = await resp.json(content_type=None)
    except TimeoutError as ex:
        raise CitycomError(-1, f"Failed to communicate with citycom API due to time out: ({str(ex)})") from ex
    except ClientError as ex:
        raise CitycomError(-1, f"Failed to communicate with citycom API due to ClientError: ({str(ex)})") from ex
    except JSONDecodeError as ex:
        raise CitycomError(-1, f"Received invalid response from citycom API: {str(ex)}") from ex

    logger.debug(f"HTTP GET Response: {json_resp}")
    if resp.status != http.HTTPStatus.OK:
        parse_error_response(resp, json_resp)

    return json_resp

async def read_user_input(prompt: str) -> str:
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)

async def send_non_json_get_request(
    session: ClientSession,
    url: str,
    timeout: Optional[int] = 60,
    headers: Optional[dict] = None,
    encoding: Optional[str] = None,
) -> str:
    try:
        if not headers:
            headers = session.headers

        if not timeout:
            timeout = session.timeout

        logger.debug(
            f"HTTP GET: {url}",
        )
        resp = await session.get(url=url, headers=headers, timeout=timeout)
        resp_content = await resp.text(encoding=encoding)
    except TimeoutError as ex:
        raise CitycomError(-1, f"Failed to communicate with citycom API due to time out: ({str(ex)})") from ex
    except ClientError as ex:
        raise CitycomError(-1, f"Failed to communicate with citycom API due to ClientError: ({str(ex)})") from ex
    except JSONDecodeError as ex:
        raise CitycomError(-1, f"Received invalid response from citycom API: {str(ex)}") from ex

    logger.debug(f"HTTP GET Response: {resp_content}")

    return resp_content


async def send_post_request(
    session: ClientSession,
    url: str,
    timeout: Optional[int] = 60,
    headers: Optional[dict] = None,
    data: Optional[dict] = None,
    json_data: Optional[dict] = None,
) -> dict[str, Any]:
    try:
        if not headers:
            headers = session.headers

        if not timeout:
            headers = session.timeout

        logger.debug(f"HTTP POST: {url}")
        #logger.debug(f"HTTP Content: {data or json_data}")

        resp = await session.post(url=url, data=data, json=json_data, headers=headers, timeout=timeout)

        json_resp: dict = await resp.json(content_type=None)
    except TimeoutError as ex:
        raise CitycomError(-1, f"Failed to communicate with citycom API due to time out: ({str(ex)})") from ex
    except ClientError as ex:
        raise CitycomError(-1, f"Failed to communicate with citycom API due to ClientError: ({str(ex)})") from ex
    except JSONDecodeError as ex:
        raise CitycomError(-1, f"Received invalid response from citycom API: {str(ex)}") from ex

    logger.debug(f"HTTP POST Response: {json_resp}")

    if resp.status != http.HTTPStatus.OK:
        parse_error_response(resp, json_resp)
    return json_resp

