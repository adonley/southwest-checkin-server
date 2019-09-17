from flask import Flask, jsonify
import redis
import os
from apscheduler.schedulers.background import BackgroundScheduler
import json
import time


r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
app = Flask(__name__)
s = BackgroundScheduler()


def check_confirmations():
    app.logger.info("Checking reservations")


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
    time.sleep(1)
    app.run(host='0.0.0.0')
