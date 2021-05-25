from binance.client import Client
from datetime import datetime, timedelta
from dotenv import dotenv_values
from env.units import SCRAP_UNITS, DEFAULT_START_DATE

import psycopg2
import sys
import time

'''
Class Description: The class is responsible for fetching previously stored data entries from the database to be returned to the client 
'''


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
    Function Description: Main function utilized to fetch data stored on database
    @return table => Table name to be queried on the database
    '''

    def run(self, table):
        conn = self.connect()
        cursor = conn.cursor()
        # This is acceptable only in this scenario as the table names are not user specifiable from the endpoints 
        # Hence, there would be little to no threat of SQL injections. 
        statement = "SELECT * FROM " + table
        data = None
        retry = 0

        # Retry funtionality when fetching data from the database 
        # The fetch will retry for a maximum of 5 times before closing the connection regardless 
        while retry != self.max_retry:
            try:
                cursor.execute(statement)
                data = cursor.fetchall()
                break
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                # Rollback SQL transactions 
                if conn:
                    conn.rollback()
                retry += 1
                print("Retry Attempt: " + str(retry) +
                      " / " + str(self.max_retry))
                # Sleep in between retries 
                time.sleep(self.retry_interval)
        if conn:
            conn.close()
        return data
