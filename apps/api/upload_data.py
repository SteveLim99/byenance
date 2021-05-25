from binance.client import Client
from datetime import datetime, timedelta
from dotenv import dotenv_values
from env.units import SCRAP_UNITS, DEFAULT_START_DATE

import psycopg2
import numpy as np
import pandas as pd
import sys

'''
Class Description: The class is responsible for running the algorithm responsible for scrapping data from the binance API. 
                   The algorithm utilizes the Kline data points provided and stores the time stamp, opening price and closing price.
'''


class UploadData():

    def __init__(self):
        super().__init__()
        api = dotenv_values("./env/api.env")
        self.client = Client(api["API"], api["SECRET"])
        db = dotenv_values("./env/db.env")
        self.db_env = {
            "host": db["POSTGRES_HOST"],
            "database": db["POSTGRES_DB"],
            "user": db["POSTGRES_USER"],
            "password": db["POSTGRES_PASSWORD"]
        }

    '''
    Function Description: A helper function utilize to connect to the PostgreSQL instance 
    @return Connection => A connection object to PostgreSQL instance is returned 
                          utilizing the environment variables set in ./env/database.env
    '''

    def connect(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.db_env)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            sys.exit(1)
        return conn

    '''
    Function Description: A helper function utilize to convert specified python datetime objects into a format 
                          understandable by the Binance API. 
    @return String => String representation of Binance API format of datetime inputs.         
    '''

    def parse_datetime(self, datetime):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return ' '.join([str(datetime.day), months[datetime.month - 1] + ',', str(datetime.year)])

    '''
    Function Description: A helper function utilize to fetch previously inserted entries on the database. 
                          This function is called in the instance where the scheduler recieves missing data points and has 
                          < 100 data points. The intuition behind fetching more legacy data from the database was that 
                          a larger dataset would provide a better approximation of the interpolation polynomial curve. Hence,
                          providing a more accurate approximation of prices at the missing data points and accomadating for statistical significance. 
    @return list => A list containing the previous 100 legacy data from the suppoesed datetime of the missing data point.       
    '''

    def get_statistical_data(self, unit, cursor):
        statement = "SELECT * from entries where unit = %s order by datetime desc limit 100"
        statistical_data = []
        cursor.execute(statement, (unit,))
        entries = cursor.fetchall()

        for entry in entries:
            opening = entry[3]
            closing = entry[4]
            # Data points excluding the opening and closing price are inserted as NaN
            # This allows us to easily filter out the added data points after interpolation 
            statistical_data.append(
                [np.nan, np.nan, opening, closing, np.nan])

        return statistical_data

    '''
    Function Description: Main function used to fetch and interpolate data from the Binance API. 
    @param unit_start_datetimes => Dictionary containing start datetime object the function should query from to update the database upon first request of the flask server and hourly updates.
                                   Start datetime object is representative of the lastest entry found in the database for each unit. 
    @param cursor => Cursor object utilized for SQL statement executions.
    @return dictionary => Dictionary containing the mapping of each unit and their respective price data stored in a dataframe.
    @return dictionary => List containing the datetime objects which are representative of a new day. A new day is defined by a data point at hour 00:00
    '''

    def get_and_interpolate(self, unit_start_datetimes, cursor):
        all_prices = {}
        # Iterate through all units defined in .env/units.py
        for unit in unit_start_datetimes.keys():
            start_date = unit_start_datetimes[unit]
            converted_start_date = self.parse_datetime(start_date)

            # Fetching historical kline data from binance api 
            klines = self.client.get_historical_klines(
                unit, Client.KLINE_INTERVAL_1HOUR, converted_start_date)

            # Iterate through data points that are already found on database based on their datetime 
            start_idx = 0
            curr_date = datetime.fromtimestamp(int(klines[start_idx][0])/1000)
            while curr_date <= start_date:
                start_idx += 1
                curr_date = datetime.fromtimestamp(
                    int(klines[start_idx][0])/1000)

            prices = []
            delta = timedelta(hours=1)
            rolling_datetimes = []

            # Initialize variable that would be used to compare difference between two datetime objects 
            # This is required as it allows us to identify and insert missing hourly data points by checking 
            # whether the time difference is more than 60 minutes 
            init = klines[start_idx]
            prev = datetime.fromtimestamp(int(init[0])/1000)
            prices.append([unit, prev, float(init[1]), float(init[2]), 0])
            missing_data_point_present = False

            for i in klines[start_idx + 1:]:
                # Replacing the current seen timestamp to only contain the hour to make for an easier comparison 
                timestamp = datetime.fromtimestamp(
                    int(i[0])/1000).replace(minute=0, second=0, microsecond=0)
                time_diff = round(int((timestamp - prev).total_seconds()) / 60)
                if timestamp.hour == 0:
                    rolling_datetimes.append(timestamp.date())

                if time_diff > 60:
                    missing_data_points = round(time_diff / 60) - 1
                    missing_data_point_present = True

                    # Inserting missing data points with NaN placeholders which are identifiable via pandas during interpolation 
                    for _ in range(missing_data_points):
                        missing_datetime = prev + delta
                        if missing_datetime.hour == 0:
                            rolling_datetimes.append(missing_datetime.date())
                        prices.append(
                            [unit, missing_datetime, np.nan, np.nan, 1])
                        prev = missing_datetime

                # Inserting current data point seen
                prices.append([unit, timestamp, float(i[1]), float(i[2]), 0])
                prev = timestamp

            # Identifying whether current data is sufficiently large to accomadate for statistical significance during interpolation 
            # If true, previously inserted data points based on the datetime are fetched and pre-pended to the list 
            appended_statistical_data = False
            if missing_data_point_present and len(prices) <= 100:
                statistical_data = self.get_statistical_data(unit, cursor)
                prices = statistical_data + prices
                appended_statistical_data = True

            # Conversion of list to a dataframe object 
            prices = pd.DataFrame(prices, dtype="float64",
                                  columns=["unit", "datetime", "opening", "closing", "interpolated"])

            # A polynomial interpolation method was chosen due to the trend of crypto prices.
            # As crypto prices are very volatile, there is not clear or visible trend of the graph.
            # Hence, we opted for a polynomial interpolation method as it would provide a better approximation of the
            # crypto price trend as compared to a linear interpolation method.
            prices["opening"] = prices["opening"].interpolate(
                method='polynomial', order=2).round(2)
            prices["closing"] = prices["closing"].interpolate(
                method='polynomial', order=2).round(2)

            # Removing previously inserted data points to accomadate for statistical significance 
            # Removal is relatively easy as all current data entries are ensured to contain a unit whereas 
            # added data entries have NaN as a unit allowing us to easily filter out added data entries. 
            if appended_statistical_data:
                prices = prices[prices['unit'].notna()]

            prices["interpolated"] = prices['interpolated'].astype(int)

            # Adding dataframe to corresponding unit key in the dictionary 
            all_prices[unit] = prices
        return (all_prices, rolling_datetimes)

    '''
    Function Description: A helper function utilize to fetch the datetime of the last inserted entry on the database for each unit 
                          found on the database. The latest datetime is utilize upon the first request called at the API upon start up
                          which would allow the database to be updated before any data is returned to the client. It should be noted that, 
                          new units specified in .env/units.py that are not found in the database will be set to the default start time specified.
    @param cursor => Cursor object utilized for SQL statement executions.
    @return dictionary => A dictionary containing the relevant start time of each units specified in .env/units.py 
    '''

    def get_latest_entry(self, cursor):
        statement = "SELECT DISTINCT ON (unit) unit, datetime FROM entries ORDER BY unit, datetime DESC"
        current_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        res = {}

        cursor.execute(statement)
        latest_entries = cursor.fetchall()
        units_present = set()

        for entry in latest_entries:
            unit = entry[0]
            latest_date = entry[1]
            units_present.add(unit)

            if current_time > latest_date:
                res[unit] = latest_date

        # units found in the database will be compared to the ones specified in .env/units.py
        # missing units will be set to default
        # this allows new units to be added in the units.py file and to be automatically ingested into our database.
        missing_units = SCRAP_UNITS - units_present
        for unit in missing_units:
            res[unit] = DEFAULT_START_DATE

        return res

    '''
    Function Description: Main function utilize to calculate the daily returns based on daily rolling hourly returns based on previously 
                          inserted daily entries for the provided date object. 
    @param end_period => date object which represents the 00:00 hour of a new day
    @param cursor => Cursor object utilized for SQL statement executions.
    @param unit => crypto unit utilized to query the database 
    @return float => float object representing rolling returns based on opening prices 
    @return float => float object representing rolling returns based on closing prices 
    '''

    def get_rolling_profit(self, end_period, cursor, unit):
        delta = timedelta(days=1)
        start_period = end_period - delta
        # Fetching previously inserted entries stored on the database 
        statement = "select         \
                        id,         \
                        datetime,   \
                        opening,    \
                        closing     \
                    from entries    \
                    where           \
                    datetime > %s   \
                    and             \
                    datetime <= %s  \
                    and             \
                    unit = %s"

        cursor.execute(statement, (start_period, end_period, unit,))
        period_entries = cursor.fetchall()
        prev_entry = period_entries[0]

        # Algorithm utilized to calculate rolling returns 
        # An iterative approach was opted for to accomadate for the hourly updates to the database 
        total_percentile_diff_open, total_percentile_diff_close = 0, 0
        for curr_entry in period_entries[1:]:
            prev_entry_open_start, prev_entry_close_start = prev_entry[2], prev_entry[3]

            total_percentile_diff_open += (
                curr_entry[2] - prev_entry_open_start) * 100 / prev_entry_open_start
            total_percentile_diff_close += (
                curr_entry[3] - prev_entry_close_start) * 100 / prev_entry_close_start

            prev_entry = curr_entry

        rolling_open = round(total_percentile_diff_open /
                             len(period_entries), 6)
        rolling_close = round(
            total_percentile_diff_close / len(period_entries), 6)
        return (rolling_open, rolling_close)

    '''
    Function Description: The main algorithm utilized to automatically populate the database with data scrapped from binance and 
                          the daily returns calculated. This algorithm is utilized in both the hourly ingest and the start up ingest 
                          which allow the database to be updated on an hourly basis and when the application first starts up. It should be
                          noted that the Connect and Cursor objects for the SQL database are specified here and passed in as parameters to the
                          respective helper functions. This prevent multiple Cursor objects to be initialize making it easier to mantain the number 
                          of active connections to the database. This is because the entire algorithm within this function is wrapped in a 
                          try, catch and finally block which will always clsoe the database connection whether the run was successful or not.
    '''

    def run(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            units_last_entries = self.get_latest_entry(cursor)

            if units_last_entries != {}:
                # fetching the hourly price entries and the rolling datetimes which will be utilized to calculated the
                # rolling daily returns
                prices, rolling_datetimes = self.get_and_interpolate(
                    units_last_entries, cursor)

                for unit in prices.keys():
                    price = prices[unit]
                    rows = price.to_numpy()
                    cols = ','.join(list(price.columns))

                    # It should be noted that all SQL statements are written as parameterised queries to prevent SQL injection attacks
                    statement = "INSERT INTO entries(%s) values(%%s, %%s, %%s, %%s, CAST(%%s as BOOLEAN))" % (
                        cols)

                    # Bulk insert of entries to reduce network transfer cost and database load
                    # this method provides significant performance benefits compared to iteratively
                    # and repetitive calls to cursor to insert entries.
                    cursor.executemany(statement, rows)

                    # Individual calculation of daily returns using an iterative approach
                    # This decision was employed to tie together with the automatic hourly updates,
                    # As hourly updates would only consist of at most one daily entry at 00:00 at any time,
                    # this will not be as performance intensive as compared to the initial bulk loading of data into the database.
                    rolling_values = []
                    for date in rolling_datetimes:
                        rolling_open, rolling_close = self.get_rolling_profit(
                            date, cursor, unit)
                        rolling_values.append(
                            [date, rolling_open, rolling_close, unit])

                    rolling_rows = np.array(rolling_values)
                    rolling_cols = ','.join(
                        ["date", "opening", "closing", "unit"])

                    rolling_statement = "INSERT INTO rolling_returns(%s) values(%%s, %%s, %%s, %%s)" % (
                        rolling_cols)

                    # Bulk insert of rolling returns
                    cursor.executemany(rolling_statement, rolling_rows)

                conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            if conn:
                conn.rollback()
        finally:
            # Close active connection to the database
            if conn:
                conn.close()
