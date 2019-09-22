from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import os
import json
import logging
import datetime

from pytz import utc

from api.southwest.southwest import Reservation
from api.southwest import checkin

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


@app.route('/confirmation', methods=['POST'])
def submit_confirmation():
    data = json.loads(request.data)

    # Validate
    errors = []
    if not data.get('firstName'):
        errors.append('provide a first name')
    if not data.get('lastName'):
        errors.append('provide a last name')
    if not data.get('confirmation'):
        # TODO: maybe check the size
        errors.append('provide a correct confirmation')
    # TODO: Validate futher?

    # Bail if we have errors
    if len(errors) > 0:
        return jsonify({"errors": errors}), 400

    notifications = []
    if data.get('email') is not None:
        notifications.append({'mediaType': 'EMAIL', 'emailAddress': data.get('email')})
    if data.get('phone') is not None:
        notifications.append({'mediaType': 'SMS', 'phoneNumber': data.get('phone')})

    reservation = Reservation(data['confirmation'], data['firstName'], data['lastName'], notifications)
    body = reservation.lookup_existing_reservation()

    # Get our local current time
    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    tomorrow = now + datetime.timedelta(days=1)
    flight_info_list = []

    # find all eligible legs for checkin
    for leg in body['bounds']:
        flight_info = {}
        # calculate departure for this leg
        airport = "{}, {}".format(leg['departureAirport']['name'], leg['departureAirport']['state'])
        takeoff = "{}-{}".format(leg['departureDate'], leg['departureTime'])
        flight_info['takeoff'] = takeoff
        flight_info['airport'] = airport
        flight_info['checked-in'] = False
        airport_tz = checkin.timezone_for_airport(leg['departureAirport']['code'])
        date = airport_tz.localize(datetime.strptime(takeoff, '%Y-%m-%d %H:%M'))
        flight_info_list.append(flight_info)

    data['flightInfo'] = flight_info_list

    # r.sadd()
    # TODO: put in key for date UTC?
    # TODO: put in for confirmation
    # TODO: key expiration?
    r.set(data.get('confirmation'), json.dumps(data))
    return jsonify(data), 201


@app.route('/confirmation/<code>', methods=['GET'])
def get_confirmation(code: str):
    app.logger.info("Get request through docker")
    confirmation = r.get(code)
    # validate existence
    if not confirmation:
        return jsonify({"errors": ["confirmation not found"]}), 400
    return confirmation.decode("utf-8"), 200


@app.route('/confirmation/<code>', methods=['DELETE'])
def delete_confirmation(code: str):
    # validate existence
    confirmation = r.get(code)
    if not confirmation:
        return jsonify({"errors": ["confirmation not found"]}), 400
    resp = r.delete(code)
    # TODO: delete from day key set.
    # No keys affected
    if int(resp) == 0:
        return jsonify({"errors": ["could not delete confirmation"]}), 500
    return confirmation.decode("utf-8"), 200


@app.route('/health', methods=['GET'])
def health():
    test_string = "I'm a goose"
    resp = r.echo(test_string)
    app.logger.info(resp)
    if resp != test_string:
        return jsonify({"status": "down"}), 500
    return jsonify({"status": "ok"}), 200


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run()
