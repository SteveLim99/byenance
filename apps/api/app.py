from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from upload_data import UploadData
from fetch_data import GetData

app = Flask(__name__)
fd = UploadData()
gd = GetData()


@app.before_first_request
def update_db():
    fd.run()


def hourly_db_update():
    fd.run()


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(hourly_db_update, 'interval', minutes=60)
scheduler.start()


@app.route("/getEntries",  methods=['GET'])
def getEntries():
    data = gd.get_data_from_db("entries")
    res = {
        'status': 'fail'
    }

    if data != None:
        entries = []

        for d in data:
            tmp = {
                'id': d[0],
                'unit': d[1],
                'datetime': d[2],
                'opening': str(d[3]),
                'closing': str(d[4]),
                'interpolated': str(d[5])
            }
            entries.append(tmp)

        res['entries'] = entries
        res['status'] = 'success'

    return jsonify(res)


@app.route("/getRollingReturns", methods=['GET'])
def getRollingReturns():
    data = gd.get_data_from_db("rolling_returns")
    res = {
        'status': 'fail'
    }

    if data != None:
        returns = []

        for d in data:
            tmp = {
                'id': d[0],
                'date': d[1],
                'opening': str(d[2]),
                'closing': str(d[3]),
                'unit': d[4]
            }
            returns.append(tmp)

        res['returns'] = returns
        res['status'] = 'success'

    return jsonify(res)
