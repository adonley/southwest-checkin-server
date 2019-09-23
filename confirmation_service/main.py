from flask import Flask, jsonify
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
import time
import datetime
import json
import requests
import threading
from pytz import utc, timezone
from confirmation_service.southwest import Reservation


r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
app = Flask(__name__)
s = BackgroundScheduler()


def timezone_for_airport(airport_code):
    tzrequest = {
        'iata': airport_code,
        'country': 'ALL',
        'db': 'airports',
        'iatafilter': 'true',
        'action': 'SEARCH',
        'offset': '0'
    }
    tzresult = requests.post("https://openflights.org/php/apsearch.php", tzrequest)
    airport_tz = timezone(json.loads(tzresult.text)['airports'][0]['tz_id'])
    return airport_tz


def checkin(flight_info):
    notifications = []
    if flight_info.get('email') is not None:
        notifications.append({'mediaType': 'EMAIL', 'emailAddress': flight_info.get('email')})
    if flight_info.get('phone') is not None:
        notifications.append({'mediaType': 'SMS', 'phoneNumber': flight_info.get('phone')})
    reservation = Reservation(flight_info['firstName'], flight_info['lastName'], flight_info['confirmation'], notifications)
    # This will try to checkin multiple times
    data = reservation.checkin()
    for flight in data['flights']:
        for doc in flight['passengers']:
            # Store that we're done
            # TODO: Get the right flight info for this leg -> check one that is close in time to parse out
            flight_info['results'].append(
                {
                    'name': doc['name'],
                    'boardingGroup': doc['boardingGroup'],
                    'boardingPosition': doc['boardingPosition']
                }
            )
            print("{} got {}{}!".format(doc['name'], doc['boardingGroup'], doc['boardingPosition']))


def check_confirmations():
    app.logger.info("checking reservations")
    days_to_check = 40
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
                    failed = info.get('failed', False)
                    utc_depart = datetime.datetime.utcfromtimestamp(info['utcDepartureTimestamp'])
                    now = datetime.datetime.utcnow()

                    if not checked_in and not failed and (utc_depart - now + datetime.timedelta(seconds=2)) < datetime.timedelta(hours=24):
                        print("{} within 24 hours, checking in.".format(confirmation_code))
                        # Checkin with a thread so everyone goes at the same time :D
                        t = threading.Thread(target=checkin, args=(confirmation_decoded, ))
                        t.daemon = True
                        t.start()
                        threads.append(t)
                    else:
                        print("{} within {} hours.".format(confirmation_code, (utc_depart - now).total_seconds() / (60*60)))

    while True:
        if len(threads) == 0:
            break
        for t in threads:
            # Cycle every 5 seconds to check if thread is still alive
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
    # Show down if we're not connected to redis or our scheduler isn't running
    if resp != test_string or not s.running:
        return jsonify({"status": "down"}), 500
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    s.add_job(check_confirmations, trigger='interval', seconds=20, max_instances=1)
    s.start()
    time.sleep(2)
    app.run(host='0.0.0.0', port=5001)
