from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from upload_data import UploadData
from fetch_data import GetData

app = Flask(__name__)
fd = UploadData()
gd = GetData()

# Upon initialization of the system, the first request will first fetch all kline data from the 
# Binance API using the default date specified in ./env/units.py
@app.before_first_request
def update_db():
    fd.run()

def hourly_db_update():
    fd.run()

# Scheduler Utilized to fetch hourly kline data points from the binance api 
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(hourly_db_update, 'interval', minutes=60)
scheduler.start()

# Endpoint used to obtain entries stored in the database 
# entries are defined as each hourly data point found via the Binance API 
@app.route("/getEntries",  methods=['GET'])
def getEntries():
    data = gd.get_data_from_db("entries")
    res = {
        'status': 'fail'
    }

    if data != None:
        entries = []

        # Data returned are formatted as a list of dictionaries to allow for easy access of data in the web application.
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

# Endpoint used to obtain daily rolling returns calculated and stored in the database
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
