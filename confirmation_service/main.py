from flask import Flask, jsonify
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
import time
import datetime
import json
import threading
from pytz import utc


r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
app = Flask(__name__)
s = BackgroundScheduler()


def check_confirmations():
    app.logger.info("checking reservations")
    days_to_check = 60
    threads = []
    current_day = datetime.datetime.combine(datetime.datetime.utcnow().date(), datetime.time(0, 0, 0), tzinfo=utc)
    # check each of the days
    for d in range(0, days_to_check):
        check_timestamp = int(datetime.datetime.timestamp(current_day + datetime.timedelta(days=d)))
        confirmations = list(r.smembers(check_timestamp))
        if len(confirmations) > 0:
            for c in confirmations:
                confirmation_decoded = json.loads(c.decode("utf-8"))
                for info in confirmation_decoded['flightInfo']:
                    confirmation_code = confirmation_decoded['confirmation']
                    checked_in = info['checkedIn']
                    utc_depart = datetime.datetime.fromtimestamp(info['utcDepartureTimestamp'])
                    now = datetime.datetime.utcnow()

                    # within 24 hour and not already checked in
                    if not checked_in and (utc_depart - now) < datetime.timedelta(hours=24):
                        print("{} within 24 hours, checking in.".format(confirmation_code))
                        # Checkin with a thread
                        t = threading.Thread(target=schedule_checkin, args=(date, r))
                        t.daemon = True
                        t.start()
                        threads.append(t)
                    else:
                        print("{} within {}.".format(confirmation_code, (utc_depart - now)))

    # cleanup threads while handling Ctrl+C
    while True:
        if len(threads) == 0:
            break
        for t in threads:
            t.join(5)
            if not t.isAlive():
                threads.remove(t)
                break

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
