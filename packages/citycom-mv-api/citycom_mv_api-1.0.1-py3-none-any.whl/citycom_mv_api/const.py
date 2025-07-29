import pytz

HEADERS_NO_AUTH = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9,he;q=0.8,ru;q=0.7",
    "dnt": "1",
    "origin": "https://citycom-mv.com",
    "referer": "https://citycom-mv.com",
    "sec-ch-ua": '"Chromium";v="121", "Not A(Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",  # noqa: E501
}

HEADERS_WITH_AUTH = HEADERS_NO_AUTH.copy()  # Make a copy of the original dictionary
HEADERS_WITH_AUTH["Authorization"] = "Bearer 1234"
HEADERS_WITH_AUTH["Cookie"] = "ARRAffinity=?; ARRAffinitySameSite=?; GCLB=?"

TIMEZONE = pytz.timezone("Asia/Jerusalem")
CITYCOM_MV_WEBSITE = "https://citycom-mv.com"

BASE_URL = f"{CITYCOM_MV_WEBSITE}/api/api"
LOGIN_URL = f"{BASE_URL}/account/login"
UPDATE_USER_LOGIN_URL = f"{BASE_URL}/user/updateUserLogin"
USER_INFO_URL = f"{BASE_URL}/user/info"
ALERT_TYPES_URL = f"{BASE_URL}/lookups/alertTypes"
NOTIFICATION_TYPES_URL = f"{BASE_URL}/lookups/notificationTypes"
TICKET_STATUS_URL = f"{BASE_URL}/lookups/ticketStatus"
ALERT_STATUS_URL = f"{BASE_URL}/lookups/alertStatus"
METER_REPLACEMENT_REASON_URL = f"{BASE_URL}/lookups/meterReplacementReason"
METER_SIZE_URL = f"{BASE_URL}/lookups/meterSize"
ACTIVE_ALERTS_URL = f"{BASE_URL}/alerts/active/{{meter_id}}"
WATER_SUMMARY_URL = f"{BASE_URL}/meterdata/water/summary/{{meter_id}}"
CONSUMPTION_URL = BASE_URL + "/meterdata/consumption/?period={time_period}&meterId={meter_id}"
CONSUMPTION_URL_DATE_PARAMS = "&fromDate={from_date}&toDate={to_date}"

ERROR_RESPONSE_DESCRIPTOR_FIELD = "error"
ERROR_RESPONSE_DESCRIPTOR_DESCRIPTION_FIELD = "error_description"
