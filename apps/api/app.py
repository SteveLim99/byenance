from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from binance.client import Client
from datetime import datetime, timedelta
from dotenv import dotenv_values
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
api = dotenv_values("../../env/api.env")

client = Client(api["API"], api["SECRET"])
app = Flask(__name__)


def sensor():
    klines = client.get_historical_klines(
        "BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 Jan, 2018")

    opening, closing = [], []
    missing, datetimes = [], []
    delta = timedelta(hours=1)
    idx = 1

    init = klines[0]
    prev = datetime.fromtimestamp(int(init[0])/1000)
    opening.append(float(init[1]))
    closing.append(float(init[2]))
    datetimes.append(prev)

    for i in klines[1:]:
        timestamp = datetime.fromtimestamp(int(i[0])/1000)
        time_diff = round(int((timestamp - prev).total_seconds()) / 60)

        if time_diff > 60:
            missing_data_points = round(time_diff / 60) - 1
            for _ in range(missing_data_points):
                opening.append(np.nan)
                closing.append(np.nan)
                missing.append(idx)

                missing_datetime = prev + delta
                datetimes.append(missing_datetime)
                prev = missing_datetime
                idx += 1

        opening.append(float(i[1]))
        closing.append(float(i[2]))
        datetimes.append(timestamp)

        idx += 1
        prev = timestamp

    values = pd.Series(opening, dtype="float64")
    values = values.interpolate(method='polynomial', order=2)
    values = values.round(2)

    for i in missing:
        print("Real: ", values[i-1])
        print("Interpolated: ", values[i])

    # plt.plot(datetimes[:150], values[-150:])
    # plt.plot(closing, timestamps)
    # plt.show()


sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor, 'interval', minutes=10)
sched.start()


@app.route("/")
def home():
    """ Function for test purposes. """
    return str(app.config["counter"])


if __name__ == "__main__":
    sensor()
