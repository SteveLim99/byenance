from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from fetch_data import FetchData

app = Flask(__name__)


@app.before_first_request
def update_db():
    fd = FetchData()
    fd.run()


def hourly_db_update():
    fd = FetchData()
    fd.run()


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(hourly_db_update, 'interval', minutes=60)
scheduler.start()


@app.route("/")
def home():
    return 'hello'
