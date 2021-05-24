from binance.client import Client
from datetime import datetime, timedelta
from dotenv import dotenv_values
from env.units import SCRAP_UNITS, DEFAULT_START_DATE

import psycopg2
import numpy as np
import pandas as pd
import sys


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

    def connect(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.db_env)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            sys.exit(1)
        return conn

    def parse_datetime(self, datetime):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return ' '.join([str(datetime.day), months[datetime.month - 1] + ',', str(datetime.year)])

    def get_statistical_data(self, unit, cursor):
        statement = "SELECT * from entries where unit = %s order by datetime desc limit 100"
        statistical_data = []
        cursor.execute(statement, (unit,))
        entries = cursor.fetchall()

        for entry in entries:
            opening = entry[3]
            closing = entry[4]
            statistical_data.append(
                [np.nan, np.nan, opening, closing, np.nan])

        return statistical_data

    def get_and_interpolate(self, unit_start_datetimes, cursor):
        all_prices = {}
        for unit in unit_start_datetimes.keys():
            start_date = unit_start_datetimes[unit]
            converted_start_date = self.parse_datetime(start_date)

            klines = self.client.get_historical_klines(
                unit, Client.KLINE_INTERVAL_1HOUR, converted_start_date)

            start_idx = 0
            curr_date = datetime.fromtimestamp(int(klines[start_idx][0])/1000)
            while curr_date <= start_date:
                start_idx += 1
                curr_date = datetime.fromtimestamp(
                    int(klines[start_idx][0])/1000)

            prices = []
            delta = timedelta(hours=1)
            rolling_datetimes = []

            init = klines[start_idx]
            prev = datetime.fromtimestamp(int(init[0])/1000)
            prices.append([unit, prev, float(init[1]), float(init[2]), 0])
            missing_data_point_present = False
            for i in klines[start_idx + 1:]:
                timestamp = datetime.fromtimestamp(
                    int(i[0])/1000).replace(minute=0, second=0, microsecond=0)
                time_diff = round(int((timestamp - prev).total_seconds()) / 60)
                if timestamp.hour == 0:
                    rolling_datetimes.append(timestamp.date())

                if time_diff > 60:
                    missing_data_points = round(time_diff / 60) - 1
                    missing_data_point_present = True

                    for _ in range(missing_data_points):
                        missing_datetime = prev + delta
                        if missing_datetime.hour == 0:
                            rolling_datetimes.append(missing_datetime.date())
                        prices.append(
                            [unit, missing_datetime, np.nan, np.nan, 1])
                        prev = missing_datetime

                prices.append([unit, timestamp, float(i[1]), float(i[2]), 0])
                prev = timestamp

            appended_statistical_data = False
            if missing_data_point_present and len(prices) <= 100:
                statistical_data = self.get_statistical_data(unit, cursor)
                prices = statistical_data + prices
                appended_statistical_data = True

            prices = pd.DataFrame(prices, dtype="float64",
                                  columns=["unit", "datetime", "opening", "closing", "interpolated"])
            prices["opening"] = prices["opening"].interpolate(
                method='polynomial', order=3).round(2)
            prices["closing"] = prices["closing"].interpolate(
                method='polynomial', order=3).round(2)

            if appended_statistical_data:
                prices = prices[prices['unit'].notna()]

            prices["interpolated"] = prices['interpolated'].astype(int)

            all_prices[unit] = prices
        return (all_prices, rolling_datetimes)

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

        missing_units = SCRAP_UNITS - units_present
        for unit in missing_units:
            res[unit] = DEFAULT_START_DATE

        return res

    def get_rolling_profit(self, end_period, cursor, unit):
        delta = timedelta(days=1)
        start_period = end_period - delta
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

    def run(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            units_last_entries = self.get_latest_entry(cursor)

            if units_last_entries != {}:
                prices, rolling_datetimes = self.get_and_interpolate(
                    units_last_entries, cursor)

                for unit in prices.keys():
                    price = prices[unit]
                    rows = price.to_numpy()
                    cols = ','.join(list(price.columns))

                    statement = "INSERT INTO entries(%s) values(%%s, %%s, %%s, %%s, CAST(%%s as BOOLEAN))" % (
                        cols)

                    cursor.executemany(statement, rows)
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

                    cursor.executemany(rolling_statement, rolling_rows)

                conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
