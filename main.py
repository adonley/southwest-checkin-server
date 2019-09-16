from flask import Flask, request, jsonify
import redis
import os
import json
import logging

app = Flask(__name__)

r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)


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
        # TODO: check size
        errors.append('provide a confirmation')
    # TODO: validate against API?
    # Bail if we have errors
    if len(errors) > 0:
        return jsonify({"errors": errors}), 400

    # r.sadd()
    # TODO: Validate
    return "", 201


@app.route('/confirmation', methods=['GET'])
def get_confirmations():
    app.logger.info("Get request through docker")
    # TODO: validate existence
    return 200


@app.route('/confirmation', methods=['DELETE'])
def delete_confirmation():
    # TODO: validate existence
    return


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
