import requests
import sys
import uuid

BASE_URL = 'https://mobile.southwest.com/api/'
CHECKIN_INTERVAL_SECONDS = 2
MAX_ATTEMPTS = 3


class Reservation(object):
    def __init__(self, number, first, last, notifications=[]):
        self.number = number
        self.first = first
        self.last = last
        self.notifications = notifications

    @staticmethod
    def generate_headers():
        config_js = requests.get('https://mobile.southwest.com/js/config.js')
        if config_js.status_code == requests.codes.ok:
            modded = config_js.text[config_js.text.index("API_KEY"):]
            API_KEY = modded[modded.index(':') + 1:modded.index(',')].strip('"')
        else:
            print("Couldn't get API_KEY")
            # TODO: Probably should not exit here
            sys.exit(1)

        # Pulled from proxying the Southwest iOS App
        return {
            'Host': 'mobile.southwest.com',
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
            'X-User-Experience-Id': str(uuid.uuid1()).upper(),
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0 Safari/537.36',
            'Accept': '*/*'
        }

    # You might ask yourself, "Why the hell does this exist?"
    # Basically, there sometimes appears a "hiccup" in Southwest where things
    # aren't exactly available 24-hours before, so we try a few times
    def safe_request(self, url, body=None):
        attempts = 0
        headers = Reservation.generate_headers()
        while True:
            if body is not None:
                r = requests.post(url, headers=headers, json=body)
            else:
                r = requests.get(url, headers=headers)
            data = r.json()
            if 'httpStatusCode' in data and data['httpStatusCode'] in ['NOT_FOUND', 'BAD_REQUEST', 'FORBIDDEN']:
                attempts += 1
                raise Exception(data['message'])
            return data

    def load_json_page(self, url, body=None):
        data = self.safe_request(url, body)
        if not data:
            return
        for k, v in list(data.items()):
            if k.endswith("Page"):
                return v

    def with_suffix(self, uri):
        return "{}{}{}?first-name={}&last-name={}".format(BASE_URL, uri, self.number, self.first, self.last)

    def lookup_existing_reservation(self):
        # Find our existing record
        return self.load_json_page(self.with_suffix("mobile-air-booking/v1/mobile-air-booking/page/view-reservation/"))

    def get_checkin_data(self):
        return self.load_json_page(self.with_suffix("mobile-air-operations/v1/mobile-air-operations/page/check-in/"))
