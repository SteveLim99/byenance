from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from fetch_data import FetchData

app = Flask(__name__)


@app.before_first_request
def update_db():
    fd = FetchData()
    fd.run("BTCUSDT")


def sensor():
    return


sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor, 'interval', minutes=10)
sched.start()


@app.route("/")
def home():
    return 'hello'
