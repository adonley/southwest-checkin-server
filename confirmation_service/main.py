from flask import Flask, jsonify
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
import time
import datetime
import json
import requests
from pytz import utc, timezone

from southwest import Reservation

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
app = Flask(__name__)
s = BackgroundScheduler()
app.logger.info("REDIS_HOST={}".format(os.environ.get('REDIS_HOST', 'localhost')))


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


def checkin(confirmation, flight_info_index):
    print("Checking in confirmation: {}".format(confirmation['confirmation']))
    reservation = Reservation(confirmation['confirmation'], confirmation['firstName'], confirmation['lastName'], [])

    # This will try to checkin multiple times
    data = None
    try:
        data = reservation.checkin()
        failed = False
    except Exception as e:
        print("Failed")
        failed = True

    confirmation['flightInfo'][flight_info_index]['failed'] = failed
    if failed:
        r.set(confirmation.get('confirmation'), json.dumps(confirmation))
        return confirmation

    confirmation['flightInfo'][flight_info_index]['checkedIn'] = True
    for flight in data['flights']:
        for doc in flight['passengers']:
            confirmation['flightInfo'][flight_info_index]['results'].append(
                {
                    'name': doc['name'],
                    'boardingGroup': doc['boardingGroup'],
                    'boardingPosition': doc['boardingPosition']
                }
            )
            app.logger.info("{} got {}{}!".format(doc['name'], doc['boardingGroup'], doc['boardingPosition']))
    r.set(confirmation.get('confirmation'), json.dumps(confirmation))
    return confirmation


def get_close_confirmations():
    days_to_check = 40
    # So we move behind one day and make sure we pick up anything we moved past
    current_day = datetime.datetime.combine(datetime.datetime.utcnow().date() - datetime.timedelta(days=1), datetime.time(0, 0, 0), tzinfo=utc)

    # check all of the days
    confirmation_numbers = set()
    for d in range(0, days_to_check):
        check_timestamp = int(datetime.datetime.timestamp(current_day + datetime.timedelta(days=d)))
        members = r.smembers(check_timestamp)
        confirmation_numbers.update(members)

    confirmations = [r.get(x) for x in confirmation_numbers]
    confirmations = [json.loads(c.decode("utf-8")) for c in confirmations]
    return confirmations


def check_confirmations():
    confirmations = get_close_confirmations()
    if len(confirmations) <= 0:
        return

    for c in confirmations:
        # TODO: Validate that the confirmation is still valid...
        index = 0
        for info in c['flightInfo']:
            confirmation_code = c['confirmation']
            checked_in = info['checkedIn']
            failed = info.get('failed', False)
            utc_depart = datetime.datetime.utcfromtimestamp(info['utcDepartureTimestamp'])
            now = datetime.datetime.utcnow()
            # Start checking in anything that is a second past the confirmation time but not after 30 mins
            time_ok = datetime.timedelta(hours=23, minutes=30) < (utc_depart - now + datetime.timedelta(seconds=1)) < datetime.timedelta(hours=24)
            if not checked_in and not failed and time_ok:
                app.logger.info("{} within 24 hours, checking in.".format(confirmation_code))
                # Checkin with a thread so everyone goes at the same time :D
                checkin(c, index)
            index += 1


@app.route('/health', methods=['GET'])
def health():
    test_string = "I'm a goose"
    resp = r.echo(test_string)
    # Show down if we're not connected to redis or our scheduler isn't running
    reasons = []
    if resp.decode("utf-8") != test_string:
        reasons.append("redis server didn't respond")
    if not s.running:
        reasons.append("checkin daemon not running")
    if len(reasons) > 0:
        return jsonify({"status": "down", "reasons": reasons}), 500
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    s.add_job(check_confirmations, trigger='interval', seconds=1, max_instances=1)
    s.start()
    time.sleep(5)
    app.run(host='0.0.0.0', port=5001)
