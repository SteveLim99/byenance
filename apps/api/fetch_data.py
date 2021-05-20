from binance.client import Client
from datetime import datetime, timedelta
from dotenv import dotenv_values
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

    def get_and_interpolate(self, unit):
        klines = self.client.get_historical_klines(
            unit, Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018")

        prices = []
        delta = timedelta(hours=1)

        init = klines[0]
        prev = datetime.fromtimestamp(int(init[0])/1000)
        prices.append([unit, prev, float(init[1]), float(init[2]), 0])

        for i in klines[1:]:
            timestamp = datetime.fromtimestamp(int(i[0])/1000)
            time_diff = round(int((timestamp - prev).total_seconds()) / 60)

            if time_diff > 60:
                missing_data_points = round(time_diff / 60) - 1

                for _ in range(missing_data_points):
                    missing_datetime = prev + delta
                    prices.append([unit, missing_datetime, np.nan, np.nan, 1])
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

        return prices

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
