import calendar

import math
import os
from datetime import timedelta, datetime
from typing import Tuple, List

import openpyxl
import pandas as pd
from dateutil.relativedelta import relativedelta
from dateutil.utils import today
from pandas import DatetimeIndex


class DateUtils:
    @staticmethod
    def is_leap_year(year: int) -> bool:
        return calendar.isleap(year)

    @staticmethod
    def get_dates_for_doy(start_year: int, end_year: int, doy: int):
        dates = []
        for year in range(start_year, end_year + 1):
            if calendar.isleap(year) and doy > 59:  # Adjust for leap years
                date = datetime(year, 1, 1) + timedelta(days=doy - 2)
            else:
                date = datetime(year, 1, 1) + timedelta(days=doy - 1)
            dates.append(date)
        return dates

    @staticmethod
    def yearly_daterange_split(date_series: pd.Series, time_delta_days=1) -> List[Tuple[datetime, datetime]]:
        """
        Splits a series of dates into consecutive ranges, and if a range exceeds one year, splits further.

        Parameters:
            date_series (pd.Series): Series of datetime objects.
            time_delta_days (int): Minimum number of days difference to keep the range.

        Returns:
            List[Tuple[datetime, datetime]]: List of (start_date, end_date) tuples.
        """
        # Convert Series to DataFrame
        df = pd.DataFrame({'dates': date_series.sort_values().reset_index(drop=True)})

        # Identify consecutive dates
        df['diff'] = df['dates'].diff().dt.days
        df['new_range'] = (df['diff'] != 1).cumsum()

        def split_ranges_exceeding_one_year(group):
            min_date = group['dates'].min()
            max_date = group['dates'].max()
            ranges = []

            while (max_date - min_date).days > 365:
                next_year_date = min_date + pd.DateOffset(years=1)
                ranges.append((min_date, next_year_date - pd.DateOffset(days=1)))
                min_date = next_year_date

            ranges.append((min_date, max_date))
            return ranges

        range_list = []
        for _, g in df.groupby('new_range'):
            range_list.extend(split_ranges_exceeding_one_year(g))

        # Filter ranges shorter than time_delta_days
        formatted_range_list = [
            (start.date(), end.date())
            for start, end in range_list
            if (end - start).days >= time_delta_days
        ]

        return formatted_range_list

    @staticmethod
    def get_date_range(no_of_days: int, date=None):
        if date is None:
            date = today()
            no_of_days = -no_of_days if no_of_days > 0 else no_of_days
        if no_of_days < 0:
            end_date = date
            start_date = end_date + timedelta(days=no_of_days)
        else:
            start_date = date
            end_date = start_date + timedelta(days=no_of_days)

        return start_date, end_date

    @staticmethod
    def Make_TimeStamps(start_date, end_date) -> DatetimeIndex:
        '''
        This function determines all time steps of which the FPAR must be downloaded
        The time stamps are 8 daily.

        Keywords arguments:
        start_date -- 'yyyy-mm-dd'
        end_date -- 'yyyy-mm-dd'
        '''

        # Define the DOY and year of the start day
        DOY = datetime.strptime(start_date, '%Y-%m-%d').timetuple().tm_yday
        Year = datetime.strptime(start_date, '%Y-%m-%d').timetuple().tm_year

        # Define the year of the end day
        YearEnd = datetime.strptime(end_date, '%Y-%m-%d').timetuple().tm_year

        # Change the DOY of the start day into a DOY of MODIS day (8-daily) and create new startdate
        DOYstart = int(math.floor(DOY / 8.0) * 8) + 1
        DOYstart = str('%s-%s' % (DOYstart, Year))
        Day = datetime.strptime(DOYstart, '%j-%Y')
        Month = '%02d' % Day.month
        Day = '%02d' % Day.day
        start_date = (str(Year) + '-' + str(Month) + '-' + str(Day))

        # Create the start and end data for the whole year
        year_start_date = pd.date_range(start_date, end_date, freq='AS')
        YearEndDate = pd.date_range(start_date, end_date, freq='A')

        # Define the amount of years that are involved
        amount_of_year = YearEnd - Year

        # If the startday is not in the same year as the enddate
        if amount_of_year > 0:
            for i in range(0, amount_of_year + 1):
                if i == 0:
                    startdate1 = start_date
                    enddate1 = YearEndDate[0]
                    dates = pd.date_range(startdate1, enddate1, freq='8D')
                if i == amount_of_year:
                    startdate1 = year_start_date[-1]
                    enddate1 = end_date
                    Dates1 = pd.date_range(startdate1, enddate1, freq='8D')
                    dates = dates.union(Dates1)
                if i != amount_of_year and i != 0:
                    startdate1 = year_start_date[i - amount_of_year - 1]
                    enddate1 = YearEndDate[i]
                    Dates1 = pd.date_range(startdate1, enddate1, freq='8D')
                    dates = dates.union(Dates1)

        # If the startday is in the same year as the enddate
        if amount_of_year == 0:
            dates = pd.date_range(start_date, end_date, freq='8D')

        return dates

    @staticmethod
    def Check_Dates(dates_8d_first: tuple):
        start_date = datetime.strftime(dates_8d_first[0], "%Y-%m-%d")
        end_date = datetime.strftime(dates_8d_first[-1], "%Y-%m-%d")

        if datetime.strptime(end_date, "%Y-%m-%d") > datetime.now() - relativedelta(days=7):
            end_date = datetime.strftime(datetime.now() - relativedelta(days=7), "%Y-%m-%d")

        return start_date, end_date

    @staticmethod
    def Make_TimeStamps(start_date, end_date):
        '''
        This function determines all time steps of which the LST must be downloaded
        The time stamps are 8 daily.

        Keywords arguments:
        Startdate -- 'yyyy-mm-dd'
        Enddate -- 'yyyy-mm-dd'
        '''

        # Define the DOY and year of the start day
        DOY = datetime.strptime(start_date, '%Y-%m-%d').timetuple().tm_yday
        Year = datetime.strptime(start_date, '%Y-%m-%d').timetuple().tm_year

        # Define the year of the end day
        YearEnd = datetime.strptime(end_date, '%Y-%m-%d').timetuple().tm_year

        # Change the DOY of the start day into a DOY of MODIS day (16-daily) and create new startdate
        DOYstart = int(math.floor(DOY / 8.0) * 8) + 1
        DOYstart = str('%s-%s' % (DOYstart, Year))
        Day = datetime.strptime(DOYstart, '%j-%Y')
        Month = '%02d' % Day.month
        Day = '%02d' % Day.day
        start_date = (str(Year) + '-' + str(Month) + '-' + str(Day))

        # Create the start and end data for the whole year
        YearStartDate = pd.date_range(start_date, end_date, freq='AS')
        YearEndDate = pd.date_range(start_date, end_date, freq='A')

        # Define the amount of years that are involved
        AmountOfYear = YearEnd - Year

        # If the startday is not in the same year as the enddate
        if AmountOfYear > 0:
            for i in range(0, AmountOfYear + 1):
                if i == 0:
                    startdate1 = start_date
                    enddate1 = YearEndDate[0]
                    dates = pd.date_range(startdate1, enddate1, freq='8D')
                if i == AmountOfYear:
                    startdate1 = YearStartDate[-1]
                    enddate1 = end_date
                    dates1 = pd.date_range(startdate1, enddate1, freq='8D')
                    dates = dates.union(dates1)
                if i != AmountOfYear and i != 0:
                    startdate1 = YearStartDate[i - AmountOfYear - 1]
                    enddate1 = YearEndDate[i]
                    dates1 = pd.date_range(startdate1, enddate1, freq='8D')
                    dates = dates.union(dates1)

        # If the startday is in the same year as the enddate
        if AmountOfYear == 0:
            dates = pd.date_range(start_date, end_date, freq='8D')

        return dates

