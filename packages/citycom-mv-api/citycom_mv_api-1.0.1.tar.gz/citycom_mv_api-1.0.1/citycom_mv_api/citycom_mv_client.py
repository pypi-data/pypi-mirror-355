import asyncio
import atexit
import datetime
from typing import Optional

import aiohttp
from aiohttp import ClientSession
from loguru import logger

from citycom_mv_api import data, login
from citycom_mv_api.models.ConsumptionTimeSeries import ConsumptionTimeSeries
from citycom_mv_api.models.CustomerInformation import CustomerInformation
from citycom_mv_api.models.exceptions import LoginError
from citycom_mv_api.models.jwt import JWT
from citycom_mv_api.models.Reading import MeterReadings
from citycom_mv_api.models.TimePeriodOptions import TimePeriodOptions


class CityComMVClient:
    """citycom mv API Client."""

    def __init__(self, username: str, password: str, session: Optional[ClientSession] = None):
        """
        Initializes the class with the provided user ID and password and optionally logs in automatically.

        Args:
        session (ClientSession): The aiohttp ClientSession object.
        username (str): The username used to log in to the citycom mv website.
        password (str): The password used to log in to the citycom mv website.
        automatically_login (bool): Whether to automatically log in the user. Default is False.
        """

        if not session:
            session = aiohttp.ClientSession()
            atexit.register(self._shutdown)

        self._session = session

        self.logged_in: bool = False  # Flag to indicate if the user is logged in
        self._token: JWT = JWT(
            access_token="", refresh_token="", token_type="", expires_in=0
        )  # Token for authentication
        self._user_name: str = username  # User ID associated with the instance
        self._password: str = password  # User passowrd with the instance

        self._login_response: Optional[str] = None  # Response from the login attempt
        self._contract_id: Optional[str] = None  # Contract ID associated with the instance
        self._meter_id: Optional[str] = None  # meter id number associated with the instance

    def _shutdown(self):
        if not self._session.closed:
            asyncio.run(self._session.close())

    # -------------
    # Data methods:
    # -------------

    async def get_customer(self) -> CustomerInformation:
        """
        Get consumer data response from Citycom API.
        :return: Customer data
        """
        await self.check_token()
        customer = await data.get_customer(self._session, self._token)
        return customer

    async def get_last_meter_reading(self, meter_id: Optional[str] = None) -> Optional[MeterReadings]:
        """
        Retrieves a last meter reading for a specific contract and user.
        Args:
            self: The instance of the class.
            meter_id (str): The id number of the meter.
        Returns:
            MeterReadings: The response containing the meter readings.
        """
        await self.check_token()
        if not meter_id:
            meter_id = self._meter_id

        assert meter_id, "meter id number must be provided"

        response = await data.get_last_meter_reading(self._session, self._token, meter_id)
        if response:
            return response

    async def get_historical_data(self,  meter_id: Optional[str] = None,
                                 time_period: TimePeriodOptions = TimePeriodOptions.DAILY,
                                 from_date: datetime =None,
                                to_date: datetime= None
                                 ) -> Optional[ConsumptionTimeSeries]:
        """
        Retrieves a last meter reading for a specific contract and user.
        Args:
            self: The instance of the class.
            meter_id (str): The id number of the meter.
        Returns:
            MeterReadings: The response containing the meter readings.
        """
        await self.check_token()
        if not meter_id:
            meter_id = self._meter_id

        assert meter_id, "meter id number must be provided"

        response = await data.get_historical_data(self._session, self._token, meter_id,time_period,from_date,to_date)
        if response:
            return response
        return None
    # ----------------
    # Login/Token Flow
    # ----------------

    async def login(self):
        """
        Login with the provided user and password.
        """
        jwt_token = await login.do_login(self._session, self._user_name, self._password)
        self._token = jwt_token
        self.logged_in = True

    async def manual_login(self):
        """
        Logs the user in by obtaining an authorization token, setting the authorization header,
        and updating the login status and token attribute.
        """
        token = await login.manual_authorization(self._session, self._user_name, self._password)
        self.logged_in = True
        self._token = token

    def get_token(self) -> JWT:
        """
        Return the JWT token.
        """
        return self._token

    async def load_jwt_token(self, token: JWT):
        """
        Set the token and mark the user as logged in.
        :param token: The new token to be set.
        :return: None
        """
        self._token = token
        if await self.check_token():
            self.logged_in = True
        else:
            raise LoginError(-1, "Invalid JWT token")

    async def check_token(self) -> bool:
        """
        Check the validity of the jwt.py token and refresh in the case of expired signature errors.
        """
        if login.is_expired(self._token) or login.is_about_to_expire(self._token):
            logger.debug("jwt.py token expired, refreshing token")
            self._token=await login.do_login(self._session, self._user_name, self._password)
        # elif login.is_about_to_expire(self._token):
        #     logger.debug("jwt.py token expired, refreshing token")
        #     self.logged_in = False
        #     await self.refresh_token()

        return True

    # citycom_mv_api returns invalid grant when called for a refresh token, so we just login again
    async def refresh_token(self):
        """
        Refresh JWT token.
        """
        self._token = await login.refresh_token(self._session, self._token)
        if self._token:
            self.logged_in = True

    async def load_token_from_file(self, file_path: str = "token.json"):
        """
        Load token from file.
        """
        self._token = await login.load_token_from_file(file_path)
        self.logged_in = True

    async def save_token_to_file(self, file_path: str = "token.json"):
        """
        Save token to file.
        """
        await login.save_token_to_file(self._token, file_path)
