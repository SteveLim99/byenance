from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from binance.client import Client
from dotenv import dotenv_values

api = dotenv_values("../../env/api.env")
client = Client(api["API"], api["SECRET"])
app = Flask(__name__)


def sensor():
    """ Function for test purposes. """
    klines = client.get_historical_klines(
        "BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 hour ago UTC")
    
    print(klines)


sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor, 'interval', minutes=10)
sched.start()


@app.route("/")
def home():
    """ Function for test purposes. """
    return str(app.config["counter"])


if __name__ == "__main__":
    sensor()
