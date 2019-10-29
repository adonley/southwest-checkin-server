from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import os
import re
import json
import logging
import datetime
import requests
from pytz import utc, timezone

from southwest import Reservation

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
recaptcha_secret = os.environ.get('RECAPTCHA_SECRET', None)
app = Flask(__name__)
# TODO: Tighten this up for deployment
cors = CORS(app, resources={r"/*": {"origins": "*"}})


class Notifications:
    @staticmethod
    def Phone(number):
        return {'mediaType': 'SMS', 'phoneNumber': number}

    @staticmethod
    def Email(email_address):
        return {'mediaType': 'EMAIL', 'emailAddress': email_address}


def verify_captcha(token: str) -> bool:
    url = "https://www.google.com/recaptcha/api/siteverify"
    response = requests.post(url=url, data={'secret': recaptcha_secret, 'response': token})
    if response.status_code != 200:
        app.logger.info("Non 200 return code from captcha api")
        return False
    body = response.json()
    return body.get('success') and 0.6 < float(body.get('score'))


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


@app.route('/confirmation/submit', methods=['POST'])
def submit_confirmation():
    data = json.loads(request.data)

    # Validate
    errors = []
    if not data.get('firstName'):
        errors.append('provide a first name')
    if not data.get('lastName'):
        errors.append('provide a last name')
    if not data.get('confirmation') or len(data.get('confirmation')) != 6:
        errors.append('provide a correct confirmation')
    recaptcha = data.get('recaptcha')
    if recaptcha is None or len(recaptcha) == 0 or not verify_captcha(recaptcha):
        return jsonify({"errors": ["recaptcha was incorrect"]}), 400
    # Don't want this to go into the database
    del data['recaptcha']

    # Bail if we have errors
    if len(errors) > 0:
        return jsonify({"errors": errors}), 400

    notifications = []
    if data.get('email') is not None:
        notifications.append({'mediaType': 'EMAIL', 'emailAddress': data.get('email')})
    if data.get('phone') is not None:
        notifications.append({'mediaType': 'SMS', 'phoneNumber': data.get('phone')})

    data['confirmation'] = data['confirmation'].upper()
    reservation = Reservation(data['confirmation'], data['firstName'], data['lastName'], notifications)

    try:
        body = reservation.lookup_existing_reservation()
    except Exception as e:
        # Couldn't find the reservation
        return jsonify({"errors": [str(e)]}), 400

    if body is None:
        app.logger.warn("body response was none from southwest API")
        return jsonify({"errors": ["could not get reservation information"]}), 400

    flight_info_list = []

    # find all eligible legs for checkin
    for leg in body['bounds']:
        flight_info = {}
        # calculate departure for this leg
        airport = "{}, {}".format(leg['departureAirport']['name'], leg['departureAirport']['state'])
        destination_airport = "{}, {}".format(leg['arrivalAirport']['name'], leg['arrivalAirport']['state'])
        takeoff = "{}-{}".format(leg['departureDate'], leg['departureTime'])
        flight_info['takeoff'] = takeoff
        flight_info['departureAirport'] = airport
        flight_info['destinationAirport'] = destination_airport
        flight_info['checkedIn'] = False
        flight_info['numberOfPeople'] = int(leg['passengerTypeCounts']['adult']) + int(leg['passengerTypeCounts']['senior'])
        flight_info['boundType'] = leg['boundType']
        flight_info['travelTime'] = leg['travelTime']
        flight_info['nextDayArrival'] = leg['isNextDayArrival']
        flight_info['arrivalTime'] = leg['arrivalTime']
        airport_tz = timezone_for_airport(leg['departureAirport']['code'])
        local_dt = airport_tz.localize(datetime.datetime.strptime(takeoff, '%Y-%m-%d-%H:%M'))
        utc_dt = local_dt.astimezone(utc)
        # Crazy converserino here
        utc_day = datetime.datetime.combine(utc_dt.date(), datetime.time(0, 0, 0), tzinfo=utc)
        flight_info['utcDepartureTimestamp'] = int(datetime.datetime.timestamp(local_dt))
        flight_info['utcDay'] = int(datetime.datetime.timestamp(utc_day))
        flight_info['results'] = []
        flight_info['failed'] = False

        flight_info_list.append(flight_info)

    data['flightInfo'] = flight_info_list

    for flight_info in flight_info_list:
        r.sadd(flight_info.get('utcDay'), data.get('confirmation'))
    r.set(data.get('confirmation').upper(), json.dumps(data))
    return jsonify(data), 201


def scan_keys(pattern, count=1000):
    result = []
    cur, keys = r.scan(cursor=0, match=pattern, count=count)
    result.extend(keys)
    while cur != 0:
        cur, keys = r.scan(cursor=cur, match=pattern, count=count)
        result.extend(keys)
    return result


@app.route('/confirmation', methods=['POST'], defaults={"code": None})
@app.route('/confirmation/<string:code>', methods=['POST'])
def get_confirmation(code: str):
    if request.data is None:
        return jsonify({"errors": ["body cannot be null"]}), 400
    data = json.loads(request.data)
    recaptcha = data.get('recaptcha')
    if recaptcha is None or len(recaptcha) == 0 or not verify_captcha(recaptcha):
        return jsonify({"errors": ["recaptcha was incorrect"]}), 400
    if code is None:
        # Get all the keys that start with characters
        keys = [k.decode("utf-8") for k in r.keys("*") if bool(re.search('^[a-zA-Z]', k.decode("utf-8")))]
        results = [r.get(k).decode("utf-8") for k in keys]
        return jsonify(results), 200
    if len(code) != 6:
        return jsonify({"errors": ["confirmation must be length six"]}), 400
    app.logger.info("Get request through docker")
    code = code.upper()
    confirmation = r.get(code)
    # validate existence
    if not confirmation:
        return jsonify({"errors": ["confirmation not found"]}), 400
    confirmation = json.loads(confirmation.decode("utf-8"))
    return jsonify(confirmation), 200


@app.route('/confirmation/<code>', methods=['DELETE'])
def delete_confirmation(code: str):
    if code is None or len(code) != 6:
        return jsonify({"errors": ["confirmation must be length six"]}), 400
    # validate existence
    code = code.upper()
    confirmation = r.get(code)
    if not confirmation:
        return jsonify({"errors": ["confirmation not found"]}), 400
    confirmation = json.loads(confirmation.decode("utf-8"))
    # Delete from the day sets
    for flight_info in confirmation['flightInfo']:
        r.srem(flight_info.get('utcDay'), json.dumps(confirmation))
    resp = r.delete(code)
    # No keys affected
    if int(resp) == 0:
        return jsonify({"errors": ["could not delete confirmation"]}), 500
    return jsonify(confirmation), 200


@app.route('/health', methods=['GET'])
def health():
    test_string = "I'm a goose"
    # Ping redis to make sure we're connected
    resp = r.echo(test_string)
    if resp.decode("utf-8") != test_string:
        return jsonify({"status": "down"}), 500
    return jsonify({"status": "ok"}), 200


# If it's being run in Gunicorn
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run()
