from binance.client import Client
from datetime import datetime, timedelta
from dotenv import dotenv_values
from env.units import SCRAP_UNITS, DEFAULT_DATE

import psycopg2
import numpy as np
import pandas as pd
import sys


class FetchData():

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

    def get_and_interpolate(self, unit_start_datetimes):
        all_prices = {}
        for key in unit_start_datetimes.keys():
            unit = key
            start_date = unit_start_datetimes[key]
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

            init = klines[start_idx]
            prev = datetime.fromtimestamp(int(init[0])/1000)
            prices.append([unit, prev, float(init[1]), float(init[2]), 0])

            for i in klines[start_idx + 1:]:
                timestamp = datetime.fromtimestamp(int(i[0])/1000)
                time_diff = round(int((timestamp - prev).total_seconds()) / 60)

                if time_diff > 60:
                    missing_data_points = round(time_diff / 60) - 1

                    for _ in range(missing_data_points):
                        missing_datetime = prev + delta
                        prices.append(
                            [unit, missing_datetime, np.nan, np.nan, 1])
                        prev = missing_datetime

                prices.append([unit, timestamp, float(i[1]), float(i[2]), 0])
                prev = timestamp

            prices = pd.DataFrame(prices, dtype="float64",
                                  columns=["unit", "datetime", "opening", "closing", "interpolated"])
            prices["opening"] = prices["opening"].interpolate(
                method='polynomial', order=3).round(2)
            prices["closing"] = prices["closing"].interpolate(
                method='polynomial', order=3).round(2)
            prices["interpolated"] = prices['interpolated'].astype(int)
            all_prices[unit] = prices

        return all_prices

    def get_latest_entry(self):
        conn = self.connect()
        cursor = conn.cursor()

        statement = "SELECT unit, datetime from entries group by unit, datetime order by datetime desc LIMIT 1"
        current_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        res = {}
        try:
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
                res[unit] = DEFAULT_DATE
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
            return res

    def run(self, unit):
        conn = self.connect()
        cursor = conn.cursor()

        prices = self.get_and_interpolate(unit)
        rows = prices.to_numpy()
        cols = ','.join(list(prices.columns))
        statement = "INSERT INTO entries(%s) values(%%s, %%s, %%s, %%s, CAST(%%s as BOOLEAN))" % (
            cols)

        try:
            cursor.executemany(statement, rows)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    fd = FetchData()
    test = fd.get_latest_entry()
    print(fd.get_and_interpolate(test))
