from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)


def sensor():
    return


sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor, 'interval', minutes=10)
sched.start()


@app.route("/")
def home():
    """ Function for test purposes. """
    return str(app.config["counter"])


if __name__ == "__main__":
    sensor()
