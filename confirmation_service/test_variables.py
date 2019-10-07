import datetime
from pytz import utc, timezone

past_take_off = datetime.datetime.now() - datetime.timedelta(minutes=10)
future_take_off = datetime.datetime.now() + datetime.timedelta(hours=25)

CLOSE_CONFIRMATIONS = [
    {
        "confirmation": "PXKJDS",
        "firstName": "Aziz",
        "lastName": "Ronald",
        "phone": "",
        "email": "",
        "flightInfo": [
            {
                "takeoff": "2019-10-24-21:05",
                "departureAirport": "San Jose, CA",
                "destinationAirport": "Las Vegas, NV",
                "checkedIn": False,
                "numberOfPeople": 2,
                "boundType": "DEPARTING",
                "travelTime": "1h 15m",
                "nextDayArrival": False,
                "arrivalTime": "22:20",
                "utcDepartureTimestamp": 1571976300,
                "utcDay": 1571961600,
                "results": [],
                "failed": False
            },
            {
                "takeoff": "2019-10-28-06:40",
                "departureAirport": "Las Vegas, NV",
                "destinationAirport": "San Jose, CA",
                "checkedIn": False,
                "numberOfPeople": 2,
                "boundType": "RETURNING",
                "travelTime": "1h 20m",
                "nextDayArrival": False,
                "arrivalTime": "08:00",
                "utcDepartureTimestamp": 1572270000,
                "utcDay": 1572220800,
                "results": [],
                "failed": False
            }
        ]
    }
]

CHECKIN_RESPONSE = {
    'flights': [
        {
            'passengers': [
                {
                    'name': 'Aziz Renaldo',
                    'boardingGroup': 'B',
                    'boardingPosition': '13'
                },
                {
                    'name': 'Anny Renaldo',
                    'boardingGroup': 'B',
                    'boardingPosition': '14'
                }
            ]
        }
    ]
}


def past_confirmation():
    for flight in CLOSE_CONFIRMATIONS:
        for f in flight['flightInfo']:
            utc_dt = past_take_off.astimezone(utc)
            utc_day = datetime.datetime.combine(utc_dt.date(), datetime.time(0, 0, 0), tzinfo=utc)
            f['utcDepartureTimestamp'] = int(datetime.datetime.timestamp(past_take_off))
            f['utcDay'] = int(datetime.datetime.timestamp(utc_day))
    return CLOSE_CONFIRMATIONS
