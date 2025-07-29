# citycom_mv_api

A python wrapper for citycom_mv api

## Module Usage

```python
import asyncio
import os

import aiohttp
from loguru import logger

from citycom_mv_api.citycom_mv_client import CityComMVClient
from citycom_mv_api.login import LoginError
from citycom_mv_api.models.exceptions import CitycomError

session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), timeout=aiohttp.ClientTimeout(total=10))
try:
    # Example of usage
    client = CityComMVClient("XXXX@citycom-mv.com", "YYY", session)

    token_json_file = "token.json"
    if os.path.exists(token_json_file):
        await client.load_token_from_file(token_json_file)
    else:
        try:
            await client.login()
            await client.save_token_to_file(token_json_file)
        except LoginError as err:
            logger.error(f"Failed Login: (Code {err.code}): {err.error}")
            raise

    # refresh token example- currently not implemented, it just logins again
    token = client.get_token()
    await client.check_token()
    new_token = client.get_token()
    if token != new_token:
        print("Token refreshed")
        await client.save_token_to_file(token_json_file)

    print("access_token: " + token.access_token)

    customer = await client.get_customer()
    print(customer)

    reading = await client.get_last_meter_reading(customer.properties[0].meters[0].meter_id)
    print(reading)

except CitycomError as err:
    logger.error(f"Error: (Code {err.code}): {err.error}")
finally:
    await session.close()