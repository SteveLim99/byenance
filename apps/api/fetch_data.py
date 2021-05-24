from binance.client import Client
from datetime import datetime, timedelta
from dotenv import dotenv_values
from env.units import SCRAP_UNITS, DEFAULT_START_DATE

import psycopg2
import sys
import time


class GetData():

    def __init__(self):
        super().__init__()
        db = dotenv_values("./env/db.env")
        self.db_env = {
            "host": db["POSTGRES_HOST"],
            "database": db["POSTGRES_DB"],
            "user": db["POSTGRES_USER"],
            "password": db["POSTGRES_PASSWORD"]
        }
        self.max_retry = 5
        self.retry_interval = 5

    def connect(self):
        conn = None
        try:
            conn = psycopg2.connect(**self.db_env)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            sys.exit(1)
        return conn

    def get_data_from_db(self, table):
        conn = self.connect()
        cursor = conn.cursor()
        data = None
        retry = 0

        while retry != self.max_retry:
            try:
                statement = "SELECT * FROM " + table + " limit 100"
                cursor.execute(statement)
                data = cursor.fetchall()
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                if conn:
                    conn.rollback()
                retry += 1
                print("Retry Attempt: " + str(retry) +
                      " / " + str(self.max_retry))
                time.sleep(self.retry_interval)
        if conn:
            conn.close()
        return data
