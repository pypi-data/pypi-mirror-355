import datetime
from typing import Optional

from aiohttp import ClientSession
from cachetools import TTLCache, cached
from loguru import logger

from citycom_mv_api import commons
from citycom_mv_api.const import (
    CONSUMPTION_URL,
    CONSUMPTION_URL_DATE_PARAMS,
    HEADERS_WITH_AUTH,
    USER_INFO_URL,
    WATER_SUMMARY_URL,
)
from citycom_mv_api.models.ConsumptionHistoryData import ConsumptionHistoryData
from citycom_mv_api.models.ConsumptionTimeSeries import ConsumptionTimeSeries
from citycom_mv_api.models.CustomerInformation import CustomerInformation
from citycom_mv_api.models.jwt import JWT
from citycom_mv_api.models.Meter import Meter
from citycom_mv_api.models.Reading import MeterReadings
from citycom_mv_api.models.TimePeriodOptions import TimePeriodOptions

cache = TTLCache(maxsize=100, ttl=900)


@cached(cache)
async def get_customer(session: ClientSession, token: JWT) -> Optional[CustomerInformation]:
    """Get customer data response from API."""
    headers = commons.add_auth_bearer_to_headers(HEADERS_WITH_AUTH, token.access_token)
    # sending get request and saving the response as response object
    response = await commons.send_get_request(session=session, url=USER_INFO_URL, headers=headers)

    logger.debug(f"Response: {response}")
    return CustomerInformation.from_dict(response)


async def get_meter_by_id(session: ClientSession, token: JWT, meter_id: str) -> Optional[Meter]:
    """Get customer data response from API."""
    customer = await get_customer(session, token)
    for current_property in customer.properties:
        for meter in current_property.meters:
            if meter.id == meter_id:
                return meter
    logger.warning(f"cannot find a meter with id: {meter_id}")
    return None


async def get_last_meter_reading(session: ClientSession, token: JWT, meter_id: str) -> MeterReadings:
    """Get Last Meter Reading data response from API."""
    headers = commons.add_auth_bearer_to_headers(HEADERS_WITH_AUTH, token.access_token)
    # sending get request and saving the response as response object
    response = await commons.send_get_request(
        session=session, url=WATER_SUMMARY_URL.format(meter_id=meter_id), headers=headers
    )

    logger.debug(f"Response: {response}")
    return MeterReadings.from_dict(response)

async def get_historical_data(session: ClientSession, token: JWT, meter_id: str,
                              time_period: TimePeriodOptions = TimePeriodOptions.DAILY,
                               from_date: datetime = None, to_date: datetime=None,
                              ) -> ConsumptionTimeSeries:
    """Get historical Meter Reading data grouped by time period response from API."""
    headers = commons.add_auth_bearer_to_headers(HEADERS_WITH_AUTH, token.access_token)
    # sending get request and saving the response as response object
    url = CONSUMPTION_URL.format(meter_id=meter_id, time_period=time_period.value)
    if(time_period == TimePeriodOptions.DAILY and from_date and to_date):
        url = f"{CONSUMPTION_URL}{CONSUMPTION_URL_DATE_PARAMS}".format(meter_id=meter_id, time_period=time_period.value,
                                                    from_date=from_date.date(), to_date=to_date.date())
    elif(time_period != TimePeriodOptions.DAILY and ( from_date or  to_date)):
        logger.warning("from_date and to_date are supported only for DAILY time period - ignored")
    response = await commons.send_get_request(
        session=session, url=url,
        headers=headers
    )

    logger.debug(f"Response: {response}")
    consumption_history_data_list = [ConsumptionHistoryData.from_dict(item) for item in response]
    time_series = ConsumptionTimeSeries()
    time_series.from_consumption_history_data(consumption_history_data_list)
    return time_series
