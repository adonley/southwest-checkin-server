from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import os
import json
import logging
import datetime
import requests
from pytz import utc, timezone

from southwest import Reservation

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


class Notifications:
    @staticmethod
    def Phone(number):
        return {'mediaType': 'SMS', 'phoneNumber': number}

    @staticmethod
    def Email(email_address):
        return {'mediaType': 'EMAIL', 'emailAddress': email_address}


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


@app.route('/confirmation', methods=['POST'])
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

    # Bail if we have errors
    if len(errors) > 0:
        return jsonify({"errors": errors}), 400

    notifications = []
    if data.get('email') is not None:
        notifications.append({'mediaType': 'EMAIL', 'emailAddress': data.get('email')})
    if data.get('phone') is not None:
        notifications.append({'mediaType': 'SMS', 'phoneNumber': data.get('phone')})

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
    r.set(data.get('confirmation'), json.dumps(data))
    return jsonify(data), 201


@app.route('/confirmation/<code>', methods=['GET'])
def get_confirmation(code: str):
    if code is None or len(code) != 6:
        return jsonify({"errors": ["confirmation must be length six"]}), 400
    app.logger.info("Get request through docker")
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
