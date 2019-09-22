from flask import Flask, jsonify
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
import time
import datetime
from pytz import utc


r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
app = Flask(__name__)
s = BackgroundScheduler()


def check_confirmations():
    app.logger.info("checking reservations")
    days_to_check = 60
    current_day = datetime.datetime.combine(datetime.datetime.utcnow().date(), datetime.time(0, 0, 0), tzinfo=utc)
    # check each of the days
    for d in range(0, days_to_check):
        check_timestamp = int(datetime.datetime.timestamp(current_day + datetime.timedelta(days=d)))
        confirmations = list(r.smembers(check_timestamp))
        print("{}: {}".format(check_timestamp, confirmations))
    # Get everything a day out and check it
    app.logger.info("done checking reservations")


@app.route('/health', methods=['GET'])
def health():
    test_string = "I'm a goose"
    resp = r.echo(test_string)
    if resp != test_string:
        return jsonify({"status": "down"}), 500
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    s.add_job(check_confirmations, trigger='interval', seconds=20, max_instances=1)
    s.start()
    time.sleep(2)
    app.run(host='0.0.0.0', port=5001)
