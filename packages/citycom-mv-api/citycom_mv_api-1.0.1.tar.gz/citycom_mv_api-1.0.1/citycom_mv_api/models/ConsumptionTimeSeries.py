from datetime import datetime
from typing import List

from citycom_mv_api.models.ConsumptionHistoryData import ConsumptionHistoryData


class ConsumptionTimeSeries:
    """
    Represents a time series of consumption data.

    Attributes:
        data (list): A list of ConsumptionDataForDate objects representing the consumption data.
    """

    def __init__(self):
        self.data = []

    def add(self, date: datetime, value: float):
        """
        Adds a new consumption data point to the time series.

        Args:
            date (datetime): The date of the consumption data point.
            value (float): The value of the consumption data point.
        """
        item = ConsumptionDataForDate(date, value)
        self.data.append(item)
        self.data.sort()

    def remove(self, date: datetime, value: float):
        """
        Removes a consumption data point from the time series.

        Args:
            date (datetime): The date of the consumption data point.
            value (float): The value of the consumption data point.
        """
        item = ConsumptionDataForDate(date, value)
        self.data.remove(item)

    def get_sorted_data(self):
        """
        Returns the consumption data sorted by date.

        Returns:
            list: A list of tuples representing the consumption data, where each tuple contains the date and value.
        """
        return [(item.date, item.value) for item in self.data]

    def from_consumption_history_data(self, consumption_history_data: List[ConsumptionHistoryData]):
        """
        Converts consumption history data to a consumption time series.

        Args:
            consumption_history_data (list): A list of ConsumptionHistoryData objects
                representing the consumption history data.
        """
        for item in consumption_history_data:
            for bucket in item.series:
                date = construct_datetime(item.date, bucket.consumption_type)
                self.add(date, bucket.value)

    def __str__(self):
        return '\n'.join(str(item) for item in self.data)

class ConsumptionDataForDate:
    def __init__(self, date: datetime, value: float):
        self.date = date
        self.value = value

    def __lt__(self, other):
        return self.date < other.date

    def __str__(self):
        return f'{self.date}: {self.value}'


def construct_datetime(s1: str, s2: str):
    date_string = s1
    if(s2.isnumeric()):
        date_string= f"{s1} {s2}"
    if(date_string.isnumeric()):
         return datetime.strptime(date_string, '%Y').date()
    elif(len(s1)==3 and not s1.isnumeric()):
        # If that fails, try to parse s1 as a date string with a month and a year
        return datetime.strptime(date_string, '%b %Y').date()
    else:
       # Try to parse s1 as a date string with a day, a month, and a year
        return datetime.strptime(date_string, '%d %b %Y').date()
