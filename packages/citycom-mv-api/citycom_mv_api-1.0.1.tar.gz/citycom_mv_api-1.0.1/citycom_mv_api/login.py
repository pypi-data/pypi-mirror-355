"""Login Module."""

import datetime
import json
from typing import Optional

import aiofiles
import pytz
from aiohttp import ClientSession
from loguru import logger

from citycom_mv_api import commons
from citycom_mv_api.const import LOGIN_URL
from citycom_mv_api.models.exceptions import LoginError
from citycom_mv_api.models.jwt import JWT


async def do_login(session: ClientSession, user_name, password: str) -> Optional[JWT]:
    """
    Perform the first login for a user.

    Args:
        session: The aiohttp ClientSession object.
        id_number (str): The user's ID number.

    Returns:
        Tuple[str, str, str]: A tuple containing the state token, factor ID, and session token.
    """

    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/plain, */*"}
        response = await commons.send_post_request(
            session, url=LOGIN_URL, headers=headers, json_data={
            "grant_type": "password",
             "username": user_name,
             "password": password
             }
        )
        # Get the first factor ID and state token
        return JWT.from_dict(response)

    except Exception as error:
        logger.warning(f"Failed at first login: {error}")
        raise LoginError(-1, "Failed at first login") from error


async def manual_authorization(session: ClientSession, user_name, password: str) -> Optional[JWT]:  # pragma: no cover
    """Get authorization token from citycom API."""
    if not user_name:
        user_name = await commons.read_user_input("Enter your user: ")
    if not password:
        password = await commons.read_user_input("Enter your password: ")
    jwt_token = await do_login(session, user_name, password)
    logger.debug(
        f"Access token: {jwt_token.access_token}\n"
        f"Refresh token: {jwt_token.refresh_token}\n"
        f"access_token: {jwt_token.access_token}"
    )
    return jwt_token


async def refresh_token(session: ClientSession, token: JWT) -> Optional[JWT]:
    """Refresh JWT token."""
    headers = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}
    data = {"refresh_token": token.refresh_token, "grant_type": "refresh_token"}
    commons.add_auth_bearer_to_headers(headers, token.access_token)
    response = await commons.send_post_request(session=session, url=LOGIN_URL, data=data, headers=headers)
    return JWT.from_dict(response)


async def save_token_to_file(token: JWT, path: str = "token.json") -> None:
    """Save token to file."""
    async with aiofiles.open(path, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(token.to_dict()))


async def load_token_from_file(path: str = "token.json") -> JWT:
    """Load token from file."""
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        contents = await f.read()
    token = json.loads(contents)
    token[".expires"] = token["expires"]

    jwt_data = JWT.from_dict(token)

    return jwt_data


def is_expired(token: JWT) -> bool:
    if token.expires is None:
        return True
    expires_at = datetime.datetime.strptime(token.expires, "%a, %d %b %Y %H:%M:%S %Z")
    expires_at = expires_at.replace(tzinfo=pytz.UTC)
    return (expires_at - datetime.datetime.now(datetime.UTC)).total_seconds() < 0


def is_about_to_expire(token: JWT) -> bool:
    if token.expires is None:
        return True
    expires_at = datetime.datetime.strptime(token.expires, "%a, %d %b %Y %H:%M:%S %Z")
    expires_at = expires_at.replace(tzinfo=pytz.UTC)
    return (expires_at - datetime.datetime.now(datetime.UTC)).total_seconds() < 300
