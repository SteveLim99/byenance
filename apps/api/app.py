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
        id, unit, datetime, opening, closing, interpolated = [], [], [], [], [], []

        for d in data:
            id.append(d[0])
            unit.append(d[1])
            datetime.append(d[2])
            opening.append(d[3])
            closing.append(d[4])
            interpolated.append(d[5])

        tmp = {}
        tmp['id'] = id
        tmp['unit'] = unit
        tmp['datetime'] = datetime
        tmp['opening'] = opening
        tmp['closing'] = closing
        tmp['interpolated'] = interpolated

        res['entries'] = tmp
        res['status'] = 'success'

    return jsonify(res)


@app.route("/getRollingReturns", methods=['GET'])
def getRollingReturns():
    data = gd.get_data_from_db("rolling_returns")
    res = {
        'status': 'fail'
    }

    if data != None:
        id, date, opening, closing, unit = [], [], [], [], []

        for d in data:
            id.append(d[0])
            date.append(d[1])
            opening.append(d[2])
            closing.append(d[3])
            unit.append(d[4])

        tmp = {}
        tmp['id'] = id
        tmp['date'] = date
        tmp['opening'] = opening
        tmp['closing'] = closing
        tmp['unit'] = unit

        res['returns'] = tmp
        res['status'] = 'success'

    return jsonify(res)
