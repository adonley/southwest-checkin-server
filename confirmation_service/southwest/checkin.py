#!/usr/bin/env python
"""Southwest Checkin.

Usage:
  checkin.py CONFIRMATION_NUMBER FIRST_NAME LAST_NAME [--email=<email_addr> | --mobile=<phone_num>] [-v | --verbose]
  checkin.py (-h | --help)
  checkin.py --version

Options:
  -h --help     Show this screen.
  -v --verbose  Show debugging information.
  --email=<email_addr>  Email address where notification will be sent to.
  --mobile=<phone_num>  Phone number where text notification will be sent to.
  --version     Show version.

"""
from datetime import datetime
from datetime import timedelta
from math import trunc
from pytz import utc
from confirmation_service.southwest import Reservation
from threading import Thread
import time
import requests
import json
import pytz

CHECKIN_EARLY_SECONDS = 5


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
    airport_tz = pytz.timezone(json.loads(tzresult.text)['airports'][0]['tz_id'])
    return airport_tz


def schedule_checkin(flight_time, reservation):
    checkin_time = flight_time - timedelta(days=1)
    current_time = datetime.utcnow().replace(tzinfo=utc)
    # check to see if we need to sleep until 24 hours before flight
    if checkin_time > current_time:
        # calculate duration to sleep
        delta = (checkin_time - current_time).total_seconds() - CHECKIN_EARLY_SECONDS
        # pretty print our wait time
        m, s = divmod(delta, 60)
        h, m = divmod(m, 60)
        print("Too early to check in.  Waiting {} hours, {} minutes, {} seconds".format(trunc(h), trunc(m), s))
        time.sleep(delta)
    data = reservation.checkin()
    for flight in data['flights']:
        for doc in flight['passengers']:
            print("{} got {}{}!".format(doc['name'], doc['boardingGroup'], doc['boardingPosition']))


def auto_checkin(reservation_number, first_name, last_name, notify=[]):
    r = Reservation(reservation_number, first_name, last_name, notify)
    body = r.lookup_existing_reservation()

    # Get our local current time
    now = datetime.utcnow().replace(tzinfo=utc)
    tomorrow = now + timedelta(days=1)

    threads = []

    # find all eligible legs for checkin
    for leg in body['bounds']:
        # calculate departure for this leg
        airport = "{}, {}".format(leg['departureAirport']['name'], leg['departureAirport']['state'])
        takeoff = "{} {}".format(leg['departureDate'], leg['departureTime'])
        airport_tz = timezone_for_airport(leg['departureAirport']['code'])
        date = airport_tz.localize(datetime.strptime(takeoff, '%Y-%m-%d %H:%M'))
        if date > now:
            # found a flight for checkin!
            print("Flight information found, departing {} at {}".format(airport, date.strftime('%b %d %I:%M%p')))
            # Checkin with a thread
            t = Thread(target=schedule_checkin, args=(date, r))
            t.daemon = True
            t.start()
            threads.append(t)

    # cleanup threads while handling Ctrl+C
    while True:
        if len(threads) == 0:
            break
        for t in threads:
            t.join(5)
            if not t.isAlive():
                threads.remove(t)
                break
